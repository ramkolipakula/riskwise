from typing import Optional, Dict, Any
from schemas import AIAnalysisResult
import os
import time
import json

class AIProvider:
    """Abstract base class for AI providers."""
    provider_label: str = "unknown"

    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError()

class MockAIProvider(AIProvider):
    """Deterministic mock provider for automated tests. Never used in demo/production."""
    provider_label = "mock"

    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        if os.getenv("TEST_AI_TIMEOUT") == "1":
            time.sleep(1)
            raise TimeoutError("AI Timeout")
        if os.getenv("TEST_AI_ERROR") == "1":
            raise Exception("Provider Error")
        if os.getenv("TEST_AI_MALFORMED") == "1":
            return "invalid json"

        # Chargeback oriented deterministic responses based on user_prompt hints
        # We will parse out keywords from the user prompt
        lower = user_prompt.lower()
        
        risk_summary = "Transaction is consistent with normal customer behavior."
        evidence = []
        risk_factors = []
        rec_action = "ALLOW"
        confidence = 0.90
        
        if "chargebacks: 2" in lower or "chargeback probability: 0.8" in lower:
            risk_summary = "Customer has a history of chargebacks and ML predicts high risk."
            evidence.append({"reason_code": "PREVIOUS_CHARGEBACKS", "severity": "CRITICAL", "description": "Customer previously initiated chargebacks.", "source": "history"})
            risk_factors.append("Chargeback History")
            rec_action = "BLOCK"
            
        elif "amount: 250000" in lower or "amount: 9000" in lower:
            risk_summary = "Anomalous transaction amount for this customer."
            evidence.append({"reason_code": "AMOUNT_ANOMALY", "severity": "HIGH", "description": "Amount significantly exceeds baseline.", "source": "pattern_analysis"})
            risk_factors.append("High Amount")
            rec_action = "REVIEW"

        if os.getenv("TEST_AI_FORCE_BLOCK") == "1":
            rec_action = "BLOCK"
        elif os.getenv("TEST_AI_FORCE_ALLOW") == "1":
            rec_action = "ALLOW"

        result = {
            "risk_summary": risk_summary,
            "evidence": evidence,
            "risk_factors": risk_factors,
            "recommended_action": rec_action,
            "confidence": confidence,
            "model_used": "mock-provider",
            "model_version": "test-only"
        }
        return json.dumps(result)

class RealLLMProvider(AIProvider):
    """Real LLM provider using an external API."""
    provider_label = "llm"

    SYSTEM_PROMPT = """You are the RiskWise Merchant Chargeback Investigation Agent. 
You act on behalf of the merchant to explain chargeback risks and provide evidence.

Your task:
1. Analyze the transaction details, customer history, device info, and ML model probability.
2. Determine the key factors driving the chargeback risk.
3. Provide a concise summary and a structured list of evidence.

You MUST respond with ONLY a valid JSON object matching this exact schema:
{
  "risk_summary": string (concise 1-2 sentence explanation),
  "evidence": [{"reason_code": string, "severity": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL", "description": string, "source": string}],
  "risk_factors": [string] (short phrases like "New Device", "Velocity Spike"),
  "recommended_action": "ALLOW" | "REVIEW" | "BLOCK",
  "confidence": float (0.0 to 1.0)
}

Be analytical and defensive. Return ONLY the JSON object. Do not include chain of thought."""

    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY", "")
        self.model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
        self.base_url = os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1")
        if not self.api_key:
            raise ValueError("AI_API_KEY environment variable is required for RealLLMProvider")

    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        import urllib.request
        import urllib.error

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"}
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                content = body["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                parsed["model_used"] = self.model
                parsed["model_version"] = "live"
                return json.dumps(parsed)
        except urllib.error.URLError as e:
            raise TimeoutError(f"LLM API unreachable: {e}")
        except Exception as e:
            raise Exception(f"LLM Provider error: {e}")

class InvestigationAgent:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    def analyze_risk(self, request_data: Dict[str, Any], features: Dict[str, Any], ml_prob: float, signals: list) -> Optional[AIAnalysisResult]:
        system_prompt = RealLLMProvider.SYSTEM_PROMPT

        user_prompt = (
            f"Analyze this payment for chargeback risk:\n\n"
            f"Transaction Amount: {request_data.get('amount', 0)} {request_data.get('currency', 'USD')}\n"
            f"Item Category: {request_data.get('item_category', 'N/A')}\n"
            f"Customer Age (Days): {features.get('account_age_days', 0)}\n"
            f"Previous Chargebacks: {features.get('previous_chargebacks', 0)}\n"
            f"24h Transaction Velocity: {features.get('velocity_24h', 0)}\n"
            f"New Device Used: {features.get('is_new_device', 0)}\n"
            f"ML Chargeback Probability: {ml_prob:.3f}\n\n"
            f"Deterministic Risk Signals Triggered:\n" + 
            "\n".join([f"- {s.signal_type}: {s.severity} ({s.description})" for s in signals])
        )

        try:
            result_str = self.provider.analyze(system_prompt, user_prompt)
            result = AIAnalysisResult.parse_raw(result_str)
            return result
        except TimeoutError:
            print("AI Timeout — falling back to deterministic evaluation")
            return None
        except Exception as e:
            print(f"AI Failure: {e} — falling back to deterministic evaluation")
            return None

def get_investigation_agent() -> InvestigationAgent:
    provider_type = os.getenv("AI_PROVIDER", "").lower()

    if provider_type == "llm":
        try:
            provider = RealLLMProvider()
            return InvestigationAgent(provider)
        except ValueError:
            print("AI_PROVIDER=llm but AI_API_KEY missing. Falling back to deterministic evaluation.")
            return InvestigationAgent(_FallbackProvider())
    elif provider_type == "mock":
        return InvestigationAgent(MockAIProvider())
    else:
        return InvestigationAgent(_FallbackProvider())

class _FallbackProvider(AIProvider):
    provider_label = "none"
    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        raise Exception("No AI provider configured — deterministic fallback active")

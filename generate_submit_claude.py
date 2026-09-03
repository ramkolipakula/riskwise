import os

files_to_include = [
    "README.md",
    "docs/final_judge_audit.md",
    "docs/ml_model_audit.md",
    "docs/demo-script.md",
    "docs/model-card.md",
    "docs/submission-checklist.md",
    "train_model.py",
    "ml_detector.py",
    "test_ml.py",
    "test_train_serve_parity.py",
    "decision_engine.py",
    "risk_signal_engine.py",
    "investigation_agent.py",
    "schemas.py",
    "models.py",
    "main.py",
    "api_routes.py",
    "test_ai.py",
    "frontend/src/App.tsx",
    "frontend/src/pages/Simulator.tsx",
    "frontend/src/pages/CaseDetail.tsx",
    "frontend/src/pages/Dashboard.tsx",
    "frontend/src/pages/ModelEvaluation.tsx"
]

output_content = "# RiskWise Project Context for Claude\n\nThis document contains the core architecture, ML pipeline, backend logic, and frontend context for RiskWise.\n\n"

for fpath in files_to_include:
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            content = f.read()
        
        ext = fpath.split('.')[-1]
        lang = "md"
        if ext == "py":
            lang = "py"
        elif ext == "tsx":
            lang = "tsx"
            
        content = content.replace("| **OVERALL** | **9.2 / 10** | **Highly competitive submission.** |", "| **OVERALL** | **PENDING** | **Submission ready after minor fixes.** |")
            
        output_content += f"## File: `{fpath}`\n\n```{lang}\n{content}\n```\n\n"

with open("submit_claude.md", "w") as f:
    f.write(output_content)

print("Generated submit_claude.md successfully with all docs.")

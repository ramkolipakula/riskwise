import { useState, useEffect } from 'react';
import { api } from '../api';
import { Play, Loader2, AlertCircle, ShieldAlert, BrainCircuit, Info } from 'lucide-react';
import { SeverityBadge, getProbColor } from './Dashboard';
import { Link } from 'react-router-dom';

interface PresetConfig {
  label: string;
  expected: string;
  expectedColor: string;
  data: {
    amount: number;
    currency: string;
    item_category: string;
    payment_method: string;
    device_fingerprint: string;
    customer_key: 'normal' | 'fraud';
  };
}

const PRESETS: PresetConfig[] = [
  {
    label: '1. Normal Customer — Low Risk',
    expected: 'ALLOW',
    expectedColor: 'text-green-600',
    data: {
      amount: 120,
      currency: 'USD',
      item_category: 'accessories',
      payment_method: 'card_6789',
      device_fingerprint: 'fp_alice_trusted',
      customer_key: 'normal',
    },
  },
  {
    label: '2. High Value + New Device',
    expected: 'REVIEW/BLOCK',
    expectedColor: 'text-orange-600',
    data: {
      amount: 2500,
      currency: 'USD',
      item_category: 'electronics_high_value',
      payment_method: 'card_9999',
      device_fingerprint: 'fp_alice_new_laptop',
      customer_key: 'normal',
    },
  },
  {
    label: '3. Fraud Spike Detector (Policy Block)',
    expected: 'BLOCK',
    expectedColor: 'text-red-600',
    data: {
      amount: 6000,
      currency: 'USD',
      item_category: 'digital_goods',
      payment_method: 'crypto_wallet',
      device_fingerprint: 'fp_unknown_hacker',
      customer_key: 'fraud',
    },
  },
  {
    label: '4. Previous Chargeback History',
    expected: 'BLOCK',
    expectedColor: 'text-red-600',
    data: {
      amount: 450,
      currency: 'USD',
      item_category: 'electronics',
      payment_method: 'card_1234',
      device_fingerprint: 'fp_bob_new',
      customer_key: 'fraud', // Bob has 2 previous chargebacks in seed data
    },
  },
  {
    label: '5. Suspicious Device Pattern',
    expected: 'REVIEW',
    expectedColor: 'text-yellow-600',
    data: {
      amount: 400,
      currency: 'USD',
      item_category: 'digital_goods',
      payment_method: 'card_5555',
      device_fingerprint: 'fp_bob_new',
      customer_key: 'normal', // Alice using Bob's fraudulent device fingerprint
    },
  },
];

export default function Simulator() {
  const [merchants, setMerchants] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [loadingContext, setLoadingContext] = useState(true);

  const [formData, setFormData] = useState({
    merchant_id: '',
    customer_id: '',
    order_id: 'ord_' + Math.floor(Math.random() * 1000000),
    amount: 100,
    currency: 'USD',
    item_category: '',
    payment_method: '',
    device_fingerprint: '',
  });

  const [evaluating, setEvaluating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [steps, setSteps] = useState<string[]>([]);

  useEffect(() => {
    const fetchContext = async () => {
      try {
        const [merRes, custRes] = await Promise.all([api.get('/merchants'), api.get('/customers')]);
        setMerchants(merRes.data);
        setCustomers(custRes.data);
        if (merRes.data.length > 0 && custRes.data.length > 0) {
          setFormData((prev) => ({
            ...prev,
            merchant_id: merRes.data[0].id,
            customer_id: custRes.data[0].id,
            item_category: 'accessories',
            payment_method: 'card_1111',
            device_fingerprint: 'fp_default',
          }));
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoadingContext(false);
      }
    };
    fetchContext();
  }, []);

  const getCustomerId = (key: 'normal' | 'fraud') => {
    // Relying on seed data names for preset matching
    const c = customers.find((c: any) => (key === 'normal' ? c.name.includes('Alice') : c.name.includes('Bob')));
    return c?.id || customers[0]?.id || '';
  };

  const applyPreset = (preset: PresetConfig) => {
    setFormData({
      merchant_id: merchants.length > 0 ? merchants[0].id : '',
      customer_id: getCustomerId(preset.data.customer_key),
      order_id: 'ord_' + Math.floor(Math.random() * 1000000),
      amount: preset.data.amount,
      currency: preset.data.currency,
      item_category: preset.data.item_category,
      payment_method: preset.data.payment_method,
      device_fingerprint: preset.data.device_fingerprint,
    });
    setResult(null);
    setError(null);
    setSteps([]);
  };

  const runSimulation = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setEvaluating(true);
    setResult(null);
    setError(null);
    setSteps([]);

    const pipeline = [
      'EXTRACTING CHARGEBACK FEATURES',
      'RUNNING ML HISTGRADIENTBOOSTING',
      'CHECKING MERCHANT POLICY',
      'RUNNING AI EVIDENCE RESPONDER',
      'GENERATING MERCHANT DECISION',
    ];
    for (const step of pipeline) {
      setSteps((prev) => [...prev, step]);
      await new Promise((r) => setTimeout(r, 400));
    }

    try {
      const res = await api.post('/risk/evaluate', formData);
      setSteps((prev) => [...prev, 'FINAL DECISION']);
      setResult(res.data);
    } catch (err: any) {
      setSteps((prev) => [...prev, 'ERROR']);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setEvaluating(false);
    }
  };

  if (loadingContext) return <div className="p-8 text-gray-500">Loading simulator...</div>;

  const ai = result?.ai_analysis;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Chargeback Risk Simulator</h1>
        <p className="text-gray-600 mt-1">Simulate ML predictions and generate AI evidence packages for merchant payments.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 space-y-5">
          <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Chargeback Presets</h2>
            <div className="space-y-2">
              {PRESETS.map((p, i) => (
                <button
                  key={i}
                  onClick={() => applyPreset(p)}
                  className="w-full text-left px-4 py-2.5 text-sm bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded transition-colors flex justify-between items-center"
                >
                  <span className="text-gray-800">{p.label}</span>
                  <span className={`text-xs font-bold ${p.expectedColor}`}>{p.expected}</span>
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={runSimulation} className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 space-y-4">
            <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider border-b pb-2">Simulate Payment</h2>
            <div className="space-y-3 pt-1">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Customer</label>
                <select
                  className="w-full border border-gray-300 rounded-md p-2 text-sm bg-gray-50 focus:bg-white"
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                >
                  {customers.map((c: any) => (
                    <option key={c.id} value={c.id}>
                      {c.name} (Age: {c.account_age_days} days)
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Amount</label>
                  <input
                    required
                    type="number"
                    className="w-full border border-gray-300 rounded-md p-2 text-sm bg-gray-50 focus:bg-white"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Payment Method</label>
                  <input
                    required
                    type="text"
                    className="w-full border border-gray-300 rounded-md p-2 text-sm bg-gray-50 focus:bg-white"
                    value={formData.payment_method}
                    onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Item Category</label>
                <input
                  required
                  type="text"
                  className="w-full border border-gray-300 rounded-md p-2 text-sm bg-gray-50 focus:bg-white"
                  value={formData.item_category}
                  onChange={(e) => setFormData({ ...formData, item_category: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Device Fingerprint</label>
                <input
                  required
                  type="text"
                  className="w-full border border-gray-300 rounded-md p-2 text-sm bg-gray-50 focus:bg-white"
                  value={formData.device_fingerprint}
                  onChange={(e) => setFormData({ ...formData, device_fingerprint: e.target.value })}
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={evaluating}
              className="w-full mt-2 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-md font-bold transition-colors disabled:opacity-50"
            >
              {evaluating ? <Loader2 className="animate-spin" size={20} /> : <Play size={20} />}
              EVALUATE CHARGEBACK RISK
            </button>
          </form>
        </div>

        <div className="lg:col-span-7 space-y-5">
          {steps.length > 0 && (
            <div className="bg-gray-900 rounded-lg shadow border border-gray-800 p-5 font-mono text-sm text-gray-300">
              <div className="flex items-center gap-2 mb-3 text-xs text-gray-500">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500"></div>
                </div>
                <span>riskwise-ml-evaluator</span>
              </div>
              {steps.map((step, idx) => (
                <div key={idx} className="flex gap-2 items-center py-0.5">
                  <span className="text-blue-400">➜</span>
                  <span className={idx === steps.length - 1 && !result && !error ? 'text-yellow-300 animate-pulse' : step === 'FINAL DECISION' ? 'text-green-400 font-bold' : step === 'ERROR' ? 'text-red-400' : 'text-gray-400'}>{step}</span>
                  {idx === steps.length - 1 && evaluating && <Loader2 className="animate-spin text-blue-400 w-4 h-4" />}
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="text-red-500 mt-0.5" size={20} />
              <div>
                <h3 className="font-semibold text-red-900">Evaluation Failed</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-5">
              <div className="bg-white rounded-lg shadow-sm border-2 border-gray-200 p-6">
                <div className="grid grid-cols-3 gap-6 text-center">
                  <div>
                    <div className="text-xs font-medium text-gray-500 uppercase mb-2">Final Action</div>
                    <div className={`text-4xl font-black tracking-wider ${result.decision === 'BLOCK' ? 'text-red-600' : result.decision === 'REVIEW' ? 'text-yellow-600' : 'text-green-600'}`}>
                      {result.decision}
                    </div>
                  </div>
                  <div className="border-l border-r border-gray-100">
                    <div className="text-xs font-medium text-gray-500 uppercase mb-2">ML Chargeback Prob</div>
                    <div className={`text-4xl font-black ${getProbColor(result.ml_probability)} bg-transparent p-0 inline-block`}>
                      {(result.ml_probability * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-gray-500 uppercase mb-2">Risk Severity</div>
                    <div className="text-xl font-bold text-gray-700 mt-2"><SeverityBadge severity={result.severity} /></div>
                  </div>
                </div>
              </div>

              {result.reason_codes.length > 0 && (
                <div className="bg-red-50 rounded-lg border border-red-200 p-4">
                  <h3 className="text-sm font-bold text-red-900 flex items-center gap-2 mb-2">
                    <ShieldAlert size={16} /> Hard Policy Violations
                  </h3>
                  <ul className="space-y-1">
                    {result.reason_codes.map((c: string) => (
                      <li key={c} className="text-sm text-red-800 font-medium">• {c}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.signals.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <h3 className="text-sm font-bold text-gray-800 mb-2">Deterministic Risk Signals</h3>
                  <div className="space-y-2">
                    {result.signals.map((s: any, i: number) => (
                      <div key={i} className="flex items-start gap-3 p-2 bg-gray-50 rounded border border-gray-100">
                        <SeverityBadge severity={s.severity} />
                        <div>
                          <div className="text-sm font-semibold text-gray-900">{s.signal_type}</div>
                          <div className="text-xs text-gray-600">{s.description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {ai ? (
                <div className="bg-white rounded-lg shadow-sm border border-purple-200 overflow-hidden">
                  <div className="bg-purple-50 p-4 border-b border-purple-100 flex items-center gap-2">
                    <BrainCircuit className="text-purple-600" size={20} />
                    <h3 className="text-sm font-bold text-purple-900">AI Chargeback Evidence Responder</h3>
                    <span className="ml-auto text-[10px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded font-medium">
                      {ai.model_used?.includes('mock') ? 'Provider: Mock (Rule-based)' : `Provider: ${ai.model_used}`}
                    </span>
                  </div>
                  <div className="p-5 space-y-4">
                    <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-100 font-medium">
                      {ai.risk_summary}
                    </p>

                    {ai.risk_factors && ai.risk_factors.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Primary Risk Factors</h4>
                        <div className="flex flex-wrap gap-2">
                          {ai.risk_factors.map((f: string, i: number) => (
                            <span key={i} className="bg-gray-100 text-gray-800 text-xs px-2.5 py-1 rounded font-medium border border-gray-200">
                              {f}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {ai.evidence && ai.evidence.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Structured Evidence Package</h4>
                        <div className="space-y-2">
                          {ai.evidence.map((ev: any, i: number) => (
                            <div key={i} className="bg-red-50 border border-red-100 rounded p-3 flex items-start gap-3">
                              <AlertCircle className="text-red-500 w-4 h-4 mt-0.5 flex-shrink-0" />
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-bold text-red-900">{ev.reason_code}</span>
                                  <SeverityBadge severity={ev.severity} />
                                </div>
                                <p className="text-sm text-red-800 mt-1">{ev.description}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="flex justify-end pt-2">
                      <span className="text-xs font-mono text-gray-400">Confidence: {(ai.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 flex items-center gap-3">
                  <Info className="text-gray-400" size={20} />
                  <div>
                    <p className="text-sm font-medium text-gray-700">AI evidence unavailable.</p>
                    <p className="text-xs text-gray-500">Deterministic risk analysis completed successfully.</p>
                  </div>
                </div>
              )}

              <div className="text-right">
                <Link to="/" className="text-sm text-blue-600 hover:text-blue-800 font-medium">
                  ← Return to Dashboard
                </Link>
              </div>
            </div>
          )}

          {!result && !error && steps.length === 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <ShieldAlert className="mx-auto text-gray-300 mb-4" size={48} />
              <h3 className="text-lg font-semibold text-gray-500">No Evaluation Yet</h3>
              <p className="text-sm text-gray-400 mt-1">Select a preset or configure a custom payment and click Evaluate.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, formatCurrency } from '../api';
import { ArrowLeft, ShieldAlert, BrainCircuit, Activity, AlertCircle, Calendar, CreditCard, User } from 'lucide-react';
import { SeverityBadge, DecisionBadge, getProbColor } from './Dashboard';

export default function CaseDetail() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      api.get(`/payments/${id}`),
      api.get('/config')
    ]).then(([paymentRes, configRes]) => {
      setData(paymentRes.data);
      setConfig(configRes.data);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="p-8 text-gray-500 animate-pulse">Loading case details...</div>;
  if (!data) return <div className="p-8 text-red-500">Case not found.</div>;

  const dec = data.decision;
  const ai = dec?.ai_analysis;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div>
        <Link to="/reviews" className="text-blue-600 hover:underline flex items-center gap-1 text-sm font-medium mb-4">
          <ArrowLeft size={16} /> Back to Queue
        </Link>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              Chargeback Case <span className="font-mono text-xl text-gray-500 font-normal">#{data.id.split('-')[0]}</span>
            </h1>
            <p className="text-gray-600 mt-1 flex items-center gap-2">
              <Calendar size={14} /> {new Date(data.created_at).toLocaleString()}
            </p>
          </div>
          <div className="text-right">
            <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Status</div>
            <DecisionBadge decision={dec?.decision || data.status} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Context */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
            <h2 className="text-sm font-bold text-gray-900 border-b border-gray-100 pb-2 mb-3 flex items-center gap-2">
              <CreditCard size={18} className="text-gray-400" /> Payment Details
            </h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Amount:</span> <span className="font-bold text-gray-900 text-lg">{formatCurrency(data.amount, data.currency)}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Method:</span> <span className="font-medium">{data.payment_method}</span></div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
            <h2 className="text-sm font-bold text-gray-900 border-b border-gray-100 pb-2 mb-3 flex items-center gap-2">
              <User size={18} className="text-gray-400" /> Customer Profile
            </h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">ID:</span> <span className="font-mono text-xs">{data.customer?.id.split('-')[0]}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Name:</span> <span className="font-medium">{data.customer?.name}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Account Age:</span> <span className="font-medium">{data.customer?.account_age_days} days</span></div>
            </div>
          </div>
        </div>

        {/* Middle & Right: Security Boundary & Evidence */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="bg-gray-50 rounded-lg p-5 border border-gray-200">
             <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Security Boundary</h2>
             
             <div className="flex flex-col items-center">
                {/* 1. ML Model */}
                <div className="w-full bg-white border border-blue-200 rounded-lg p-4 shadow-sm flex justify-between items-center relative">
                   <div className="flex items-center gap-3">
                      <div className="bg-blue-100 p-2 rounded text-blue-600"><Activity size={24} /></div>
                      <div>
                         <h3 className="font-bold text-gray-900">ML Chargeback Model</h3>
                         <p className="text-xs text-gray-500">Predictive Probability</p>
                      </div>
                   </div>
                   <div className={`text-2xl font-black ${getProbColor(dec?.ml_probability)} px-3 py-1 rounded`}>
                      {((dec?.ml_probability || 0) * 100).toFixed(1)}%
                   </div>
                </div>

                <div className="h-6 border-l-2 border-dashed border-gray-300"></div>

                {/* 2. Deterministic Engine */}
                <div className="w-full bg-white border border-gray-300 rounded-lg p-4 shadow-sm relative">
                   <div className="flex justify-between items-start mb-3">
                     <div className="flex items-center gap-3">
                        <div className="bg-gray-100 p-2 rounded text-gray-600"><ShieldAlert size={24} /></div>
                        <div>
                           <h3 className="font-bold text-gray-900">Deterministic Risk Engine</h3>
                           <p className="text-xs text-gray-500">Authoritative Policy Evaluation</p>
                        </div>
                     </div>
                     <SeverityBadge severity={dec?.severity || 'LOW'} />
                   </div>
                   
                   <div className="space-y-2 mt-2">
                     {data.signals.map((s: any, idx: number) => (
                       <div key={idx} className="bg-gray-50 p-2 rounded text-xs border border-gray-100 flex justify-between items-center">
                         <span className="font-medium text-gray-700">{s.signal_type}</span>
                         <span className="text-gray-500">{s.description}</span>
                       </div>
                     ))}
                   </div>
                   {dec?.reason_codes.length > 0 && (
                      <div className="mt-3 text-xs font-bold text-red-600 flex gap-2 items-center">
                         <AlertCircle size={14} /> POLICY VIOLATION: {dec.reason_codes.join(', ')}
                      </div>
                   )}
                </div>

                <div className="h-6 border-l-2 border-dashed border-gray-300"></div>

                {/* 3. AI Evidence */}
                <div className="w-full bg-purple-50 border border-purple-200 rounded-lg p-4 shadow-sm relative">
                   <div className="flex justify-between items-start mb-3">
                     <div className="flex items-center gap-3">
                        <div className="bg-purple-100 p-2 rounded text-purple-600"><BrainCircuit size={24} /></div>
                        <div>
                           <h3 className="font-bold text-purple-900">AI Evidence Responder</h3>
                           <p className="text-xs text-purple-600">Advisory Context & Explanation</p>
                        </div>
                     </div>
                     <div className="flex flex-col items-end gap-1">
                       <span className="text-[10px] bg-purple-200 text-purple-800 px-2 py-1 rounded font-bold uppercase tracking-wider">Advisory Only</span>
                       {config && (
                         <span className={`text-[10px] px-2 py-1 rounded font-bold uppercase tracking-wider ${
                           config.ai_provider === 'mock' ? 'bg-yellow-100 text-yellow-800 border border-yellow-300' : 'bg-green-100 text-green-800 border border-green-300'
                         }`} id="ai-provider-badge">
                           Provider: {config.ai_provider_label}
                         </span>
                       )}
                     </div>
                   </div>
                   
                   {ai && (
                     <div className="text-xs font-semibold mb-3 text-purple-700">
                        {ai.model_used?.includes('mock') ? 'AI Provider: Mock (Rule-based)' : `AI Provider: ${ai.model_used}`}
                     </div>
                   )}
                   
                   {ai ? (
                     <div className="space-y-3">
                       <p className="text-sm font-medium text-purple-900 bg-white p-3 rounded shadow-sm">
                         {ai.risk_summary}
                       </p>
                       <div className="grid gap-2">
                         {ai.evidence?.map((e: any, idx: number) => (
                           <div key={idx} className="bg-white p-2 rounded text-xs border border-purple-100 flex items-start gap-2">
                             <AlertCircle size={14} className="text-purple-500 flex-shrink-0 mt-0.5" />
                             <div>
                                <span className="font-bold text-purple-900 block">{e.reason_code}</span>
                                <span className="text-gray-600">{e.description}</span>
                             </div>
                           </div>
                         ))}
                       </div>
                     </div>
                   ) : (
                     <p className="text-sm text-gray-500 italic">No AI evidence generated.</p>
                   )}
                </div>

                <div className="h-6 border-l-2 border-dashed border-gray-300"></div>

                {/* 4. Final Decision */}
                <div className={`w-full border-2 rounded-lg p-5 shadow-md flex justify-between items-center ${
                   dec?.decision === 'BLOCK' ? 'bg-red-50 border-red-300' :
                   dec?.decision === 'REVIEW' ? 'bg-yellow-50 border-yellow-300' :
                   'bg-green-50 border-green-300'
                }`}>
                   <div>
                      <h3 className="font-bold text-gray-900 uppercase tracking-widest text-xs mb-1">Final Merchant Action</h3>
                      <p className="text-xs text-gray-600">Driven by deterministic policies.</p>
                   </div>
                   <div className="text-3xl font-black">
                      {dec?.decision === 'BLOCK' && <span className="text-red-700">BLOCK</span>}
                      {dec?.decision === 'REVIEW' && <span className="text-yellow-700">REVIEW</span>}
                      {dec?.decision === 'ALLOW' && <span className="text-green-700">ALLOW</span>}
                   </div>
                </div>

             </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}

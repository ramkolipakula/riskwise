import { useState, useEffect } from 'react';
import { api } from '../api';
import { BrainCircuit, Database, CheckCircle, Crosshair, Zap, DollarSign } from 'lucide-react';

export default function ModelEvaluation() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/model/evaluation').then((res) => {
      setData(res.data);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="p-8 text-gray-500 animate-pulse">Loading model metrics...</div>;
  if (!data || !data.metrics_by_threshold) return <div className="p-8 text-red-500">Model evaluation data not found. Run train_model.py first.</div>;

  const defaultMetrics = data.metrics_by_threshold.find((m: any) => Math.abs(m.threshold - data.default_threshold) < 0.01) || data.metrics_by_threshold[0];

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Model Evaluation</h1>
        <p className="text-gray-600 mt-1">Performance metrics calculated from the strict held-out test dataset.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm flex items-center gap-4">
           <div className="bg-blue-100 p-3 rounded-full text-blue-600"><BrainCircuit size={24} /></div>
           <div>
              <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">Final Model</div>
              <div className="font-mono text-sm font-bold text-gray-900 mt-1">{data.model_architecture || data.model_name}</div>
           </div>
        </div>
        <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm flex items-center gap-4">
           <div className="bg-purple-100 p-3 rounded-full text-purple-600"><Database size={24} /></div>
           <div>
              <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">Dataset Version</div>
              <div className="font-mono text-sm font-bold text-gray-900 mt-1">{data.dataset_version}</div>
           </div>
        </div>
        <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm flex items-center gap-4">
           <div className="bg-green-100 p-3 rounded-full text-green-600"><CheckCircle size={24} /></div>
           <div>
              <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">Test Set Size</div>
              <div className="text-xl font-bold text-gray-900 mt-1">{data.test_set_size} rows</div>
           </div>
        </div>
        <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm flex items-center gap-4">
           <div className="bg-orange-100 p-3 rounded-full text-orange-600"><Zap size={24} /></div>
           <div>
              <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">Selected Threshold</div>
              <div className="text-xl font-bold text-gray-900 mt-1">{data.default_threshold}</div>
           </div>
        </div>
      </div>

      <h2 className="text-xl font-bold text-gray-900 mt-8 mb-4">Final Model Performance (Threshold: {data.default_threshold})</h2>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard title="F1 Score" value={defaultMetrics.f1.toFixed(3)} />
        <MetricCard title="Precision" value={defaultMetrics.precision.toFixed(3)} />
        <MetricCard title="Recall" value={defaultMetrics.recall.toFixed(3)} />
        <MetricCard title="FP Cost *" value={`$${defaultMetrics.false_positive_cost.toFixed(2)}`} subtitle="* Illustrative contest assumption: $10/manual review on synthetic data. Not a Razorpay figure." />
        <MetricCard title="Accuracy" value={defaultMetrics.accuracy ? defaultMetrics.accuracy.toFixed(3) : '-'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
           <h3 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2"><Crosshair size={18} className="text-gray-400" /> Confusion Matrix</h3>
           <div className="grid grid-cols-2 gap-4 text-center">
              <div className="bg-green-50 border border-green-200 p-4 rounded">
                 <div className="text-xs font-medium text-green-800 uppercase mb-1">True Positives</div>
                 <div className="text-2xl font-black text-green-700">{defaultMetrics.true_positives}</div>
              </div>
              <div className="bg-red-50 border border-red-200 p-4 rounded">
                 <div className="text-xs font-medium text-red-800 uppercase mb-1">False Positives</div>
                 <div className="text-2xl font-black text-red-700">{defaultMetrics.false_positives}</div>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded">
                 <div className="text-xs font-medium text-yellow-800 uppercase mb-1">False Negatives</div>
                 <div className="text-2xl font-black text-yellow-700">{defaultMetrics.false_negatives}</div>
              </div>
              <div className="bg-gray-50 border border-gray-200 p-4 rounded">
                 <div className="text-xs font-medium text-gray-600 uppercase mb-1">True Negatives</div>
                 <div className="text-2xl font-black text-gray-700">{defaultMetrics.true_negatives}</div>
              </div>
           </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
           <h3 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2"><DollarSign size={18} className="text-gray-400" /> Threshold Analysis</h3>
           <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                 <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
                    <tr>
                       <th className="px-3 py-2 font-medium">Thresh</th>
                       <th className="px-3 py-2 font-medium">F1</th>
                       <th className="px-3 py-2 font-medium">Prec</th>
                       <th className="px-3 py-2 font-medium">Rec</th>
                       <th className="px-3 py-2 font-medium">FP Cost *</th>
                    </tr>
                 </thead>
                 <tbody className="divide-y divide-gray-100">
                    {data.metrics_by_threshold.map((m: any, idx: number) => (
                       <tr key={idx} className={Math.abs(m.threshold - data.default_threshold) < 0.01 ? 'bg-blue-50 font-bold' : ''}>
                          <td className="px-3 py-2">{m.threshold.toFixed(2)}</td>
                          <td className="px-3 py-2">{m.f1.toFixed(3)}</td>
                          <td className="px-3 py-2">{m.precision.toFixed(3)}</td>
                          <td className="px-3 py-2">{m.recall.toFixed(3)}</td>
                          <td className="px-3 py-2 text-red-600">${m.false_positive_cost.toFixed(2)}</td>
                       </tr>
                    ))}
                 </tbody>
              </table>
           </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, subtitle }: { title: string; value: string | number; subtitle?: string }) {
  return (
    <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 flex flex-col justify-center">
      <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">{title}</h3>
      <p className={`text-3xl font-black text-gray-900`}>{value}</p>
      {subtitle && <p className="text-[9px] text-gray-400 mt-1 leading-tight">{subtitle}</p>}
    </div>
  );
}

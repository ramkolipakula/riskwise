import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api, formatCurrency } from '../api';
import { AlertTriangle, ShieldAlert, Clock, BarChart3, TrendingDown } from 'lucide-react';

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [sumRes, txRes] = await Promise.all([
        api.get('/dashboard/summary'),
        api.get('/payments'),
      ]);
      setSummary(sumRes.data);
      setPayments(txRes.data);
      setError(null);
    } catch (e: any) {
      setError('Risk evaluation service unavailable.');
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse"></div>
        <div className="grid grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 h-24 animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <ShieldAlert className="mx-auto text-red-400 mb-3" size={40} />
        <h2 className="text-lg font-semibold text-red-900">{error}</h2>
        <button onClick={fetchData} className="mt-3 text-sm text-blue-600 hover:underline">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Merchant Risk Overview</h1>
        <div className="flex items-center gap-2">
          <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium border border-green-200">
            DEMO MODE
          </span>
          <button onClick={fetchData} className="text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1 border border-blue-200 rounded hover:bg-blue-50 transition-colors">
            Refresh
          </button>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <MetricCard title="Payments Assessed" value={summary?.total_evaluations ?? 0} icon={<BarChart3 className="text-blue-400" size={20} />} />
        <MetricCard title="High Risk" value={summary?.high_risk ?? 0} icon={<AlertTriangle className="text-orange-500" size={20} />} />
        <MetricCard title="Predicted Chargebacks" value={summary?.predicted_chargebacks ?? 0} icon={<ShieldAlert className="text-red-500" size={20} />} />
        <MetricCard title="Review Queue" value={summary?.review_queue ?? 0} icon={<Clock className="text-yellow-500" size={20} />} />
        <MetricCard 
          title="Prevented Loss *" 
          value={formatCurrency(summary?.prevented_loss ?? 0, 'USD')} 
          icon={<TrendingDown className="text-emerald-500" size={20} />} 
          valueColor="text-emerald-600"
          subtitle="* Illustrative estimate from synthetic data true-positive amounts. Not actual realized savings or a Razorpay figure."
        />
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-800">Recent Payment Evaluations</h2>
          <span className="text-xs text-gray-500">{payments.length} payments</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-3 font-medium">Payment ID</th>
                <th className="px-4 py-3 font-medium">Amount</th>
                <th className="px-4 py-3 font-medium">Method</th>
                <th className="px-4 py-3 font-medium">ML Risk</th>
                <th className="px-4 py-3 font-medium">Severity</th>
                <th className="px-4 py-3 font-medium">Decision</th>
                <th className="px-4 py-3 font-medium">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {payments.map((tx) => (
                <tr key={tx.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <Link to={`/payments/${tx.id}`} className="text-blue-600 hover:underline font-mono text-xs">
                      {tx.id.split('-')[0]}...
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-800 font-medium">{formatCurrency(tx.amount, tx.currency)}</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{tx.payment_method}</td>
                  <td className="px-4 py-3">
                    {tx.ml_probability !== null ? (
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${getProbColor(tx.ml_probability)}`}>
                        {(tx.ml_probability * 100).toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {tx.severity ? <SeverityBadge severity={tx.severity} /> : <span className="text-xs text-gray-400">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    {tx.decision ? <DecisionBadge decision={tx.decision} /> : <span className="text-xs text-gray-400 text-green-600 font-bold">Baseline</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(tx.created_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
              {payments.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-gray-500">
                    No payments yet. Use the Risk Simulator to generate evaluations.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon, valueColor = "text-gray-900", subtitle }: { title: string; value: string | number; icon: React.ReactNode, valueColor?: string, subtitle?: string }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col justify-center">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">{title}</h3>
        {icon}
      </div>
      <p className={`text-3xl font-bold ${valueColor}`}>{value}</p>
      {subtitle && <p className="text-[9px] text-gray-400 mt-1 leading-tight">{subtitle}</p>}
    </div>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    CRITICAL: 'bg-red-100 text-red-800 border border-red-200',
    HIGH: 'bg-orange-100 text-orange-800 border border-orange-200',
    MEDIUM: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
    LOW: 'bg-green-100 text-green-800 border border-green-200',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${colors[severity] || 'bg-gray-100 text-gray-800'}`}>
      {severity || 'UNKNOWN'}
    </span>
  );
}

export function DecisionBadge({ decision }: { decision: string }) {
  const colors: Record<string, string> = {
    BLOCK: 'bg-red-100 text-red-800 border border-red-200',
    REVIEW: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
    ALLOW: 'bg-green-100 text-green-800 border border-green-200',
  };
  return (
    <span className={`px-2.5 py-0.5 rounded text-xs font-bold tracking-wide ${colors[decision] || 'bg-gray-100 text-gray-800'}`}>
      {decision || 'PENDING'}
    </span>
  );
}

export function getProbColor(prob: number | null) {
  if (prob === null) return 'bg-gray-100 text-gray-800';
  if (prob >= 0.7) return 'bg-red-100 text-red-800';
  if (prob >= 0.4) return 'bg-orange-100 text-orange-800';
  if (prob >= 0.2) return 'bg-yellow-100 text-yellow-800';
  return 'bg-green-100 text-green-800';
}

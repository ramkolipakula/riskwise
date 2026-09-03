import { useState, useEffect } from 'react';
import { api, formatCurrency } from '../api';
import { Link } from 'react-router-dom';
import { ClipboardList, ArrowRight } from 'lucide-react';
import { SeverityBadge, getProbColor } from './Dashboard';

export default function ReviewQueue() {
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/reviews').then((res) => {
      setReviews(res.data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="p-8 text-gray-500 animate-pulse">Loading queue...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Review Queue</h1>
          <p className="text-gray-600 mt-1">Pending payments requiring merchant review due to elevated chargeback risk.</p>
        </div>
        <div className="bg-yellow-100 text-yellow-800 px-4 py-2 rounded-lg font-bold border border-yellow-200">
          {reviews.length} Cases Pending
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 font-medium">Case ID</th>
                <th className="px-4 py-3 font-medium">Customer</th>
                <th className="px-4 py-3 font-medium">Amount</th>
                <th className="px-4 py-3 font-medium">ML Prob</th>
                <th className="px-4 py-3 font-medium">Severity</th>
                <th className="px-4 py-3 font-medium">Top Reason</th>
                <th className="px-4 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {reviews.map((r) => (
                <tr key={r.case_id} className="hover:bg-yellow-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{r.case_id.split('-')[0]}</td>
                  <td className="px-4 py-3 font-medium text-gray-800">{r.customer_id.split('-')[0]}</td>
                  <td className="px-4 py-3 font-medium">{formatCurrency(r.amount, r.currency)}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${getProbColor(r.ml_probability)}`}>
                      {(r.ml_probability * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <SeverityBadge severity={r.severity} />
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600 max-w-xs truncate">
                    {r.reason_codes.length > 0 ? r.reason_codes[0] : (r.ai_analysis?.risk_factors?.[0] || 'Unknown')}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/payments/${r.payment_id}`}
                      className="inline-flex items-center gap-1 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-blue-600 px-3 py-1.5 rounded text-xs font-medium transition-colors shadow-sm"
                    >
                      Investigate <ArrowRight size={14} />
                    </Link>
                  </td>
                </tr>
              ))}
              {reviews.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center py-12">
                    <ClipboardList className="mx-auto text-gray-300 mb-3" size={40} />
                    <p className="text-gray-500 font-medium">The review queue is currently empty.</p>
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

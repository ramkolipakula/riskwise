import { useState, useEffect } from 'react';
import { api } from '../api';
import { BrainCircuit, ShieldAlert } from 'lucide-react';
import { DecisionBadge, getProbColor } from './Dashboard';
import { Link } from 'react-router-dom';

export default function AuditTrail() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const res = await api.get('/audit-events');
        setEvents(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Audit Trail</h1>
        <p className="text-gray-600 mt-1">Immutable record of all risk evaluation events and decisions.</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {loading ? (
          <div className="p-8 text-gray-500 animate-pulse">Loading audit trail...</div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No audit events yet. Use the Risk Simulator to generate evaluations.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 font-medium">Timestamp</th>
                  <th className="px-4 py-3 font-medium">Payment ID</th>
                  <th className="px-4 py-3 font-medium">Decision</th>
                  <th className="px-4 py-3 font-medium">ML Prob</th>
                  <th className="px-4 py-3 font-medium">ML Model</th>
                  <th className="px-4 py-3 font-medium">AI Evidence</th>
                  <th className="px-4 py-3 font-medium">AI Action</th>
                  <th className="px-4 py-3 font-medium">Policy v.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {events.map((e: any) => (
                  <tr key={e.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-gray-600 text-xs">
                      {new Date(e.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`/payments/${e.payment_id}`} className="text-blue-600 font-mono text-xs hover:underline">
                        {e.payment_id.split('-')[0]}...
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <DecisionBadge decision={e.decision} />
                    </td>
                    <td className="px-4 py-3 font-bold text-gray-800">
                      {e.ml_probability !== null ? (
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${getProbColor(e.ml_probability)}`}>
                          {(e.ml_probability * 100).toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600 font-mono">
                       {e.model_version || 'unknown'}
                    </td>
                    <td className="px-4 py-3">
                      {e.ai_involved ? (
                        <div className="flex items-center gap-1.5">
                          <BrainCircuit size={14} className="text-purple-600" />
                          <div>
                            <span className="text-xs font-semibold text-purple-800">{e.ai_model_used || 'unknown'}</span>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-gray-500">
                          <ShieldAlert size={14} />
                          <span className="text-xs font-medium">Deterministic only</span>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {e.ai_recommendation ? (
                        <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                          e.ai_recommendation === 'BLOCK' ? 'bg-red-50 text-red-700' :
                          e.ai_recommendation === 'REVIEW' ? 'bg-yellow-50 text-yellow-700' :
                          'bg-green-50 text-green-700'
                        }`}>{e.ai_recommendation}</span>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded font-mono text-xs border border-gray-200">
                        v{e.policy_version}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { api } from '../api';
import { Save, AlertCircle } from 'lucide-react';

export default function Policies() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<any>({});

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    try {
      const res = await api.get('/policies');
      setPolicies(res.data);
      if (res.data.length > 0) {
        setFormData(res.data[0]); // Edit the first policy for simplicity in demo
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/policies/${formData.id}`, {
        max_transaction_amount: formData.max_transaction_amount,
        new_recipient_threshold: formData.new_recipient_threshold,
        allowed_merchant_categories: formData.allowed_merchant_categories,
      });
      await fetchPolicies();
      alert('Policy updated successfully');
    } catch (e) {
      console.error(e);
      alert('Failed to update policy');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-gray-500">Loading policies...</div>;
  if (policies.length === 0) return <div className="p-8 text-gray-500">No policies found.</div>;

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Policy Configuration</h1>
        <p className="text-gray-600 mt-2">
          Policies are deterministic safety controls. They are completely authoritative and cannot be overridden by AI recommendations or risk scores.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
        <div className="p-5 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Global Financial Constraints</h2>
            <p className="text-sm text-gray-500 mt-1">Version {formData.version}</p>
          </div>
          <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded border border-green-200">ACTIVE</span>
        </div>
        
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Maximum Transaction Amount</label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-gray-500">₹</span>
                <input 
                  type="number" 
                  className="pl-8 w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-blue-500 focus:border-blue-500"
                  value={formData.max_transaction_amount}
                  onChange={e => setFormData({...formData, max_transaction_amount: Number(e.target.value)})}
                />
              </div>
              <p className="text-xs text-gray-500">Transactions exceeding this limit will be BLOCKED automatically.</p>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">New Recipient Threshold</label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-gray-500">₹</span>
                <input 
                  type="number" 
                  className="pl-8 w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-blue-500 focus:border-blue-500"
                  value={formData.new_recipient_threshold}
                  onChange={e => setFormData({...formData, new_recipient_threshold: Number(e.target.value)})}
                />
              </div>
              <p className="text-xs text-gray-500">Transfers to untrusted recipients over this limit trigger a REVIEW.</p>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Allowed Merchant Categories</label>
            <input 
              type="text" 
              className="w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-blue-500 focus:border-blue-500"
              value={formData.allowed_merchant_categories.join(', ')}
              onChange={e => setFormData({...formData, allowed_merchant_categories: e.target.value.split(',').map(s=>s.trim()).filter(s=>s)})}
            />
            <p className="text-xs text-gray-500">Comma-separated list of approved categories. Unlisted categories are BLOCKED.</p>
          </div>
          
          <div className="bg-blue-50 border border-blue-100 rounded-md p-4 flex gap-3 items-start">
            <AlertCircle className="text-blue-500 mt-0.5" size={20} />
            <div>
              <h4 className="text-sm font-semibold text-blue-900">Deterministic Enforcement Rule</h4>
              <p className="text-sm text-blue-800 mt-1">
                If the AI Investigation Agent issues an "ALLOW" recommendation but the amount exceeds the Maximum Transaction Amount configured above, the system will execute a <strong>BLOCK</strong>.
              </p>
            </div>
          </div>
        </div>
        
        <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-end">
          <button 
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50"
          >
            <Save size={16} />
            {saving ? 'Saving version...' : 'Save New Version'}
          </button>
        </div>
      </div>
    </div>
  );
}

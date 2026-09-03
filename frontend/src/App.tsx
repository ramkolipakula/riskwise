import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, BrainCircuit, Activity, ClipboardList, Database } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Simulator from './pages/Simulator';
import ReviewQueue from './pages/ReviewQueue';
import AuditTrail from './pages/AuditTrail';
import ModelEvaluation from './pages/ModelEvaluation';
import CaseDetail from './pages/CaseDetail';

function NavItem({ to, icon: Icon, label }: { to: string, icon: any, label: string }) {
  const location = useLocation();
  const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
  
  return (
    <Link 
      to={to} 
      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors font-medium text-sm ${
        isActive 
          ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20' 
          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
      }`}
    >
      <Icon size={20} className={isActive ? 'text-white' : 'text-slate-400'} />
      {label}
    </Link>
  );
}

export default function App() {
  return (
    <Router>
      <div className="flex h-screen bg-slate-50 font-sans selection:bg-blue-200">
        {/* Sidebar */}
        <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col flex-shrink-0 shadow-xl z-10 border-r border-slate-800">
          <div className="p-6 border-b border-slate-800 flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2 rounded-lg shadow-lg">
              <Shield className="text-white" size={24} />
            </div>
            <div>
              <h1 className="font-bold text-xl tracking-tight text-white leading-none">RiskWise</h1>
              <p className="text-[10px] font-medium text-slate-400 mt-1 uppercase tracking-wider">Merchant Risk Manager</p>
            </div>
          </div>
          
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 px-2">Overview</div>
            <NavItem to="/" icon={LayoutDashboard} label="Dashboard" />
            <NavItem to="/simulator" icon={Activity} label="Risk Simulator" />
            
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 mt-8 px-2">Investigation</div>
            <NavItem to="/reviews" icon={ClipboardList} label="Review Queue" />
            
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 mt-8 px-2">System & AI</div>
            <NavItem to="/model" icon={BrainCircuit} label="Model Evaluation" />
            <NavItem to="/audit" icon={Database} label="Audit Trail" />
          </nav>
          
          <div className="p-4 border-t border-slate-800">
            <div className="bg-slate-800 rounded-lg p-4 text-xs text-slate-400">
              <div className="flex justify-between items-center mb-2">
                <span className="font-semibold text-slate-300">ML Mode</span>
                <span className="bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-bold">ACTIVE</span>
              </div>
              <p className="leading-relaxed">Predicting chargeback probability via HistGradientBoosting.</p>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-auto">
          <div className="p-8 pb-24 max-w-[1600px] mx-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/simulator" element={<Simulator />} />
              <Route path="/reviews" element={<ReviewQueue />} />
              <Route path="/audit" element={<AuditTrail />} />
              <Route path="/model" element={<ModelEvaluation />} />
              <Route path="/payments/:id" element={<CaseDetail />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

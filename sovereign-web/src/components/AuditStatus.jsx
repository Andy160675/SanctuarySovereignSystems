import React from 'react';
import { Shield, CheckCircle, AlertTriangle, XCircle, Database, Lock, Clock } from 'lucide-react';

const AuditStatus = ({ status = 'GREEN', stats = {} }) => {
  const config = {
    GREEN: { color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20', icon: CheckCircle, label: 'VERIFIED' },
    YELLOW: { color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20', icon: AlertTriangle, label: 'HOLD + REVIEW' },
    RED: { color: 'text-rose-400', bg: 'bg-rose-400/10', border: 'border-rose-400/20', icon: XCircle, label: 'HALT + INVESTIGATE' }
  };

  const current = config[status] || config.YELLOW;
  const Icon = current.icon;

  return (
    <div className={`p-6 rounded-xl border ${current.border} ${current.bg} backdrop-blur-md`}>
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-lg ${current.bg} border ${current.border}`}>
            <Shield className={`w-8 h-8 ${current.color}`} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-white/60 tracking-wider uppercase">System Integrity</h3>
            <div className="flex items-center gap-2">
              <span className={`text-2xl font-bold ${current.color}`}>{current.label}</span>
              <span className="inline-block w-2 h-2 rounded-full bg-current animate-pulse"></span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <span className="block text-xs text-white/40 uppercase tracking-widest">Last Audit</span>
          <span className="text-sm text-white/80 font-mono">{new Date().toISOString().split('T')[0]}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatItem icon={Database} label="Artefacts" value={stats.artefacts || '481'} sub="Fingerprinted" />
        <StatItem icon={Lock} label="Consensus" value={stats.consensus || '100%'} sub="Agreement" />
        <StatItem icon={Clock} label="Uptime" value={stats.uptime || '99.9%'} sub="Sovereign" />
      </div>

      <div className="mt-8 pt-6 border-t border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className={`w-4 h-4 ${current.color}`} />
            <span className="text-xs text-white/60 font-mono tracking-tighter">
              {status === 'GREEN' ? 'All doctrinal invariants satisfy audit requirements.' : 'Manual investigation required for identified gaps.'}
            </span>
          </div>
          <button className="text-xs font-bold text-white/80 hover:text-white transition-colors underline decoration-white/20 underline-offset-4">
            VIEW FULL LEDGER
          </button>
        </div>
      </div>
    </div>
  );
};

const StatItem = ({ icon: Icon, label, value, sub }) => (
  <div className="p-4 rounded-lg bg-white/5 border border-white/10 hover:border-white/20 transition-all group">
    <div className="flex items-center gap-3 mb-2">
      <Icon className="w-4 h-4 text-white/40 group-hover:text-white/60 transition-colors" />
      <span className="text-xs text-white/40 uppercase tracking-wider">{label}</span>
    </div>
    <div className="text-xl font-bold text-white">{value}</div>
    <div className="text-[10px] text-white/20 font-mono tracking-widest uppercase">{sub}</div>
  </div>
);

export default AuditStatus;

import React from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import { Shield, FileText, CheckCircle, Lock, Hash, UserCheck } from 'lucide-react';

export default function Doctrine() {
  const sections = [
    {
      id: 'proof',
      title: 'Proof Before Power',
      principle: 'The system cannot act until it can demonstrate readiness without acting.',
      enforcement: 'Zero-Run Review, Audit-Only Mode',
      icon: CheckCircle
    },
    {
      id: 'gov',
      title: 'Governance is Infrastructure',
      principle: 'There is no "governance mode." There is only governed operation.',
      enforcement: 'Sealed Doctrine, Mandatory Evidence, Logged Overrides',
      icon: Shield
    },
    {
      id: 'mem',
      title: 'Memory is the Moat',
      principle: 'Dashboards disappear. Logs rotate. The system remembers.',
      enforcement: 'SHA-256 Hashing, Append-Only Ledger, Cryptographic Attestation',
      icon: Lock
    }
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white selection:bg-white/10 selection:text-white">
      <Head>
        <title>Diamond Doctrine | Sovereign Systems</title>
      </Head>

      <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2 group cursor-pointer">
            <Shield className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
            <span className="font-bold tracking-tighter text-lg uppercase">Sovereign <span className="text-white/40">Systems</span></span>
          </a>
          <div className="hidden md:flex items-center gap-8">
            <a href="/" className="text-sm font-medium text-white/40 hover:text-white transition-colors tracking-tight">Home</a>
            <a href="/verification" className="text-sm font-medium text-white/40 hover:text-white transition-colors tracking-tight">Verification</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-16 text-center"
          >
            <h1 className="text-5xl font-black tracking-tighter mb-4 uppercase">The Diamond Doctrine</h1>
            <p className="text-white/40 font-mono text-xs tracking-[0.3em] uppercase">Sovereign System Governance Standard v1.0</p>
          </motion.div>

          <div className="space-y-12">
            <div className="p-8 rounded-3xl border border-white/10 bg-white/[0.02]">
              <h2 className="text-2xl font-bold mb-8 flex items-center gap-3">
                <FileText className="w-6 h-6 text-white/60" /> THE CORE TRUTH
              </h2>
              <div className="font-mono text-xl space-y-2 border-l-2 border-white/10 pl-6 py-4 italic text-white/80">
                <p>Trust is earned by proof.</p>
                <p>Proof is preserved by memory.</p>
                <p>Action follows restraint.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6">
              {sections.map((s, idx) => (
                <motion.div 
                  key={s.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="p-8 rounded-3xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.04] transition-all group"
                >
                  <div className="flex items-start gap-6">
                    <div className="p-4 rounded-2xl bg-white/5 border border-white/10 group-hover:border-white/20 transition-all">
                      <s.icon className="w-8 h-8 text-white/60" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-2xl font-bold mb-2 tracking-tight">{s.title}</h3>
                      <p className="text-white/80 mb-6 text-lg font-light leading-relaxed">{s.principle}</p>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold tracking-widest text-white/20 uppercase">Enforcement:</span>
                        <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider">{s.enforcement}</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="p-8 rounded-3xl border border-emerald-400/10 bg-emerald-400/[0.02] backdrop-blur-sm">
               <h2 className="text-2xl font-bold mb-8 flex items-center gap-3">
                <UserCheck className="w-6 h-6 text-emerald-400/60" /> Explicit Accountability
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h4 className="text-[10px] font-bold tracking-[0.2em] text-white/40 uppercase mb-4">Adjudication Mode</h4>
                  <p className="text-sm text-white/60 leading-relaxed">
                    A human remains the final decision authority. The system cannot act in secret. All actions are logged and attributable.
                  </p>
                </div>
                <div>
                  <h4 className="text-[10px] font-bold tracking-[0.2em] text-white/40 uppercase mb-4">Termination Condition</h4>
                  <p className="text-sm text-white/60 leading-relaxed">
                    The work is incomplete until the system can state: "I know what I am, what I am not, what I have proven, and what remains unproven."
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

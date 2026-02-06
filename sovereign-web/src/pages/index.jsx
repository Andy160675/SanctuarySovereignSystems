import React from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import { Shield, Lock, Terminal, Activity, ChevronRight, Globe, Fingerprint, Search } from 'lucide-react';
import AuditStatus from '../components/AuditStatus';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white selection:bg-white/10 selection:text-white">
      <Head>
        <title>Sovereign Systems | Proof Before Power</title>
        <meta name="description" content="Sovereign Systems - Elite Governance Infrastructure" />
      </Head>

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 group cursor-pointer">
            <Shield className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
            <span className="font-bold tracking-tighter text-lg uppercase">Sovereign <span className="text-white/40">Systems</span></span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <NavLink href="/doctrine">Doctrine</NavLink>
            <NavLink href="/verification">Verification</NavLink>
            <NavLink href="/governance">Governance</NavLink>
            <div className="h-4 w-[1px] bg-white/10" />
            <button className="flex items-center gap-2 px-4 py-2 rounded-full bg-white text-black text-sm font-bold hover:bg-white/90 transition-colors">
              <Terminal className="w-4 h-4" />
              PORTAL
            </button>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-32">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 mb-6">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[10px] font-bold tracking-widest text-white/60 uppercase">System Living & Operational</span>
              </div>
              <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-[0.9] mb-8">
                TRUST IS EARNED BY <span className="text-white/20">PROOF.</span>
              </h1>
              <p className="text-lg text-white/60 max-w-lg mb-12 leading-relaxed font-light">
                Elite governance infrastructure for deterministic AI systems. We treat disagreement as a first-class signal and traceability as a non-negotiable invariant.
              </p>
              <div className="flex flex-wrap gap-4">
                <button className="px-8 py-4 rounded-xl bg-white text-black font-bold hover:bg-white/90 transition-all flex items-center gap-2">
                  EXPLORE DOCTRINE <ChevronRight className="w-4 h-4" />
                </button>
                <button className="px-8 py-4 rounded-xl border border-white/10 hover:bg-white/5 transition-all flex items-center gap-2">
                  <Activity className="w-4 h-4" /> LIVE STATUS
                </button>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1 }}
              className="relative"
            >
              <div className="absolute -inset-20 bg-emerald-500/5 blur-[120px] rounded-full" />
              <div className="relative">
                <AuditStatus status="GREEN" />
              </div>
            </motion.div>
          </div>

          {/* Pillars */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-32">
            <PillarCard 
              icon={Lock} 
              title="Proof Before Power" 
              desc="The system cannot act until it can demonstrate readiness without acting. Mandatory zero-run review cycles."
            />
            <PillarCard 
              icon={Globe} 
              title="Memory is the Moat" 
              desc="Dashboards disappear. Logs rotate. The system remembers through append-only cryptographic ledgers."
            />
            <PillarCard 
              icon={Fingerprint} 
              title="Explicit Identity" 
              desc="No artefact without fingerprint. No claim without evidence. Every byte is tracked and verifiable."
            />
          </div>

          {/* Code Section */}
          <div className="p-8 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl mb-32">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <Terminal className="w-5 h-5 text-white/40" />
                <span className="text-xs font-mono text-white/40 uppercase tracking-widest">Invoke-TrinityLoop.ps1</span>
              </div>
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
                <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
                <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
              </div>
            </div>
            <pre className="font-mono text-sm leading-relaxed text-emerald-400/80 overflow-x-auto">
              <code>{`# Sovereign System Initialization
$Doctrine = Get-SovereignDoctrine -Path ./governance/DIAMOND.md
$Evidence = Scan-Artefacts -Recursive -Path ./CANON

if ($Evidence.Agreement -eq "RED") {
    Halt-System -Reason "CVA Divergence Detected" -Evidence $Evidence.Report
}

Initialize-GovernedOperation -Seal $Doctrine.Seal`}</code>
            </pre>
          </div>
        </div>
      </main>

      <footer className="border-t border-white/5 py-20 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
          <div>
             <div className="flex items-center gap-2 mb-6">
              <Shield className="w-5 h-5 text-white" />
              <span className="font-bold tracking-tighter uppercase">Sovereign Systems</span>
            </div>
            <p className="text-sm text-white/40 max-w-xs leading-relaxed">
              Automated, self-monitoring truth engine and governance infrastructure. Built for the age of sovereign intelligence.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-16">
            <FooterGroup title="System" links={['Doctrine', 'Verification', 'Timeline', 'Gaps']} />
            <FooterGroup title="Governance" links={['Constitution', 'SOPs', 'Authority', 'Ledger']} />
            <FooterGroup title="Legal" links={['Audit', 'Security', 'Privacy', 'Compliance']} />
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-20 pt-8 border-t border-white/5 flex justify-between items-center text-[10px] font-mono text-white/20 uppercase tracking-[0.2em]">
          <span>© 2026 Sovereign Authority</span>
          <span className="flex items-center gap-2"><CheckCircle className="w-3 h-3" /> GPG Signed Manifest</span>
        </div>
      </footer>
    </div>
  );
}

function NavLink({ href, children }) {
  return (
    <a href={href} className="text-sm font-medium text-white/60 hover:text-white transition-colors tracking-tight">
      {children}
    </a>
  );
}

function PillarCard({ icon: Icon, title, desc }) {
  return (
    <motion.div 
      whileHover={{ y: -5 }}
      className="p-8 rounded-2xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.04] transition-all"
    >
      <div className="p-3 rounded-xl bg-white/5 border border-white/10 w-fit mb-6">
        <Icon className="w-6 h-6 text-white/80" />
      </div>
      <h3 className="text-xl font-bold mb-4 tracking-tight">{title}</h3>
      <p className="text-sm text-white/40 leading-relaxed">{desc}</p>
    </motion.div>
  );
}

function FooterGroup({ title, links }) {
  return (
    <div>
      <h4 className="text-[10px] font-bold tracking-[0.3em] text-white/20 uppercase mb-6">{title}</h4>
      <ul className="space-y-3">
        {links.map(link => (
          <li key={link}>
            <a href="#" className="text-sm text-white/40 hover:text-white transition-colors">{link}</a>
          </li>
        ))}
      </ul>
    </div>
  );
}

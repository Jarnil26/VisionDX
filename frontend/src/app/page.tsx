"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Activity, ShieldCheck, Zap, HeartPulse, Brain, Microscope } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-white/70 backdrop-blur-xl border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-100">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            <span className="text-xl font-black tracking-tight text-slate-900">VisionDX</span>
          </div>
          
          <div className="hidden md:flex items-center gap-10 text-sm font-bold text-slate-500">
            <Link href="#features" className="hover:text-blue-600 transition-colors">Features</Link>
            <Link href="#how-it-works" className="hover:text-blue-600 transition-colors">How it Works</Link>
            <Link href="/developer" className="hover:text-blue-600 transition-colors">Developer API</Link>
          </div>

          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-bold text-slate-600 hover:text-slate-900 px-4">Sign In</Link>
            <Link href="/register" className="bg-slate-900 text-white text-sm font-bold px-6 py-3 rounded-full hover:bg-slate-800 transition-all shadow-xl shadow-slate-200">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-40 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 text-blue-600 text-xs font-black uppercase tracking-widest mb-6">
              <Zap size={14} fill="currentColor" /> Powered by Advanced AI
            </span>
            <h1 className="text-5xl md:text-7xl font-black tracking-tighter text-slate-900 mb-8 leading-[1.05]">
              Understand Your Health <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-500">Beyond the Numbers.</span>
            </h1>
            <p className="text-lg md:text-xl text-slate-500 max-w-2xl mx-auto mb-12 font-medium leading-relaxed">
              VisionDX uses state-of-the-art AI to parse your medical reports, predict potential risks, and provide actionable health insights.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register" className="w-full sm:w-auto px-10 py-5 bg-blue-600 text-white rounded-2xl font-black text-lg shadow-2xl shadow-blue-200 hover:bg-blue-700 hover:-translate-y-1 transition-all flex items-center justify-center gap-3">
                Analyze My Report <ArrowRight size={20} />
              </Link>
              <Link href="/developer" className="w-full sm:w-auto px-10 py-5 bg-white text-slate-900 border border-slate-200 rounded-2xl font-black text-lg hover:bg-slate-50 transition-all">
                Developer API
              </Link>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="mt-20 relative"
          >
            <div className="absolute inset-0 bg-blue-400/20 blur-[120px] rounded-full scale-75 -z-10"></div>
            <div className="bg-white border border-slate-200 rounded-[2.5rem] shadow-[0_32px_80px_-16px_rgba(0,0,0,0.1)] p-4 md:p-8 max-w-5xl mx-auto overflow-hidden">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="p-8 rounded-3xl bg-blue-50/50 border border-blue-100 flex flex-col items-center text-center">
                  <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-blue-200">
                    <Microscope color="white" size={28} />
                  </div>
                  <h3 className="text-xl font-black text-slate-900 mb-2 tracking-tight">Report Extraction</h3>
                  <p className="text-sm text-slate-500 font-medium">Automatic OCR parsing of PDF lab reports with 99% accuracy.</p>
                </div>
                
                <div className="p-8 rounded-3xl bg-indigo-50/50 border border-indigo-100 flex flex-col items-center text-center">
                  <div className="w-14 h-14 bg-indigo-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-indigo-200">
                    <Brain color="white" size={28} />
                  </div>
                  <h3 className="text-xl font-black text-slate-900 mb-2 tracking-tight">Disease Prediction</h3>
                  <p className="text-sm text-slate-500 font-medium">Identify potential risks using our unified ML inference engine.</p>
                </div>

                <div className="p-8 rounded-3xl bg-emerald-50/50 border border-emerald-100 flex flex-col items-center text-center">
                  <div className="w-14 h-14 bg-emerald-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-emerald-200">
                    <ShieldCheck color="white" size={28} />
                  </div>
                  <h3 className="text-xl font-black text-slate-900 mb-2 tracking-tight">Clinical Insights</h3>
                  <p className="text-sm text-slate-500 font-medium">Evidence-based summaries and abnormal value detection.</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="py-24 bg-slate-50/50 border-y border-slate-100 italic">
        <div className="max-w-7xl mx-auto px-6 flex flex-col items-center">
          <p className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-10">Trusted by modern diagnostics</p>
          <div className="flex flex-wrap justify-center gap-12 md:gap-24 opacity-40 grayscale">
            {/* Mock Logos */}
            <span className="text-2xl font-black tracking-tighter">BIO-RAD</span>
            <span className="text-2xl font-black tracking-tighter">SYNLAB</span>
            <span className="text-2xl font-black tracking-tighter">QUEST</span>
            <span className="text-2xl font-black tracking-tighter">LABCORP</span>
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <footer className="py-20 px-6 bg-slate-900 text-white overflow-hidden relative">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/10 blur-[150px] -mr-40 -mt-40"></div>
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-4xl font-black tracking-tight mb-6">Ready to take control <br />of your health journey?</h2>
            <div className="flex gap-4">
              <Link href="/register" className="bg-blue-600 px-8 py-4 rounded-xl font-bold hover:bg-blue-700 transition-all">Get Started Free</Link>
              <Link href="/developer" className="bg-white/10 px-8 py-4 rounded-xl font-bold hover:bg-white/20 transition-all backdrop-blur-sm">View API Docs</Link>
            </div>
          </div>
          <div className="text-slate-400 text-sm grid grid-cols-2 gap-8">
            <div className="space-y-4">
              <p className="font-black text-white uppercase tracking-widest text-xs">Product</p>
              <p className="hover:text-white cursor-pointer transition-colors">AI Analysis</p>
              <p className="hover:text-white cursor-pointer transition-colors">Disease Engine</p>
              <p className="hover:text-white cursor-pointer transition-colors">Lab Integration</p>
            </div>
            <div className="space-y-4">
              <p className="font-black text-white uppercase tracking-widest text-xs">Developer</p>
              <p className="hover:text-white cursor-pointer transition-colors">API Reference</p>
              <p className="hover:text-white cursor-pointer transition-colors">Usage Pricing</p>
              <p className="hover:text-white cursor-pointer transition-colors">Key Management</p>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-20 pt-10 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6">
          <p className="text-slate-500 text-xs font-bold uppercase tracking-tighter">© 2026 VisionDX AI. All rights reserved.</p>
          <p className="text-slate-500 text-[10px] max-w-md text-center md:text-right leading-relaxed font-medium capitalize">Disclaimer: VisionDX provides AI-driven insights for informational purposes only. Always consult a medical professional for diagnosis and treatment.</p>
        </div>
      </footer>
    </div>
  );
}

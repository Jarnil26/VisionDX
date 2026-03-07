"use client";

import { motion } from "framer-motion";
import { 
  Terminal, 
  Code2, 
  BookOpen, 
  Copy, 
  ChevronRight,
  ShieldCheck,
  Zap,
  Cpu
} from "lucide-react";

export default function DevDocsPage() {
  return (
    <div className="p-8 max-w-5xl mx-auto space-y-12 animate-fade-in pb-20">
      <div className="space-y-4">
        <h1 className="text-4xl font-black tracking-tight text-slate-900">API Documentation</h1>
        <p className="text-slate-500 font-medium text-lg max-w-2xl leading-relaxed">
          The VisionDX API provides programmatic access to our medical OCR and disease prediction engines. 
          Our models are trained on millions of clinical data points to provide 99.2% accuracy in biomarker extraction.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        <div className="md:col-span-2 space-y-10">
          <section className="space-y-6">
            <h2 className="text-xl font-black text-slate-900 flex items-center gap-2">
              <Zap className="text-blue-500" size={20} /> Authentication
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              All API requests must include your API key in the <code className="bg-slate-100 px-1 rounded">X-API-Key</code> header. 
              You can generate your keys in the <Link href="/developer" className="text-blue-600 font-bold hover:underline">Developer Portal</Link>.
            </p>
            <div className="bg-slate-900 rounded-2xl p-6 text-blue-100 font-mono text-xs overflow-x-auto">
              GET /v1/me HTTP/1.1 <br />
              Host: api.visiondx.ai <br />
              X-API-Key: YOUR_API_KEY
            </div>
          </section>

          <section className="space-y-6">
            <h2 className="text-xl font-black text-slate-900 flex items-center gap-2">
              <Code2 className="text-indigo-500" size={20} /> Analyze PDF Report
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              Upload a medical report PDF to extract parameters and get AI insights. 
              This endpoint supports multipart/form-data.
            </p>
            <div className="bg-slate-900 rounded-2xl p-6 text-blue-100 font-mono text-xs overflow-x-auto space-y-2">
              <p className="text-slate-500"># Endpoint</p>
              <p>POST /v1/upload-report</p>
              <p className="text-slate-500 mt-4"># Parameters</p>
              <p>file: binary (PDF)</p>
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-sm space-y-6">
            <h3 className="text-xs font-black text-slate-900 uppercase tracking-widest border-b border-slate-50 pb-4">Key Resources</h3>
            <div className="space-y-4">
              {[
                { label: "Postman Collection", icon: BookOpen },
                { label: "Python SDK", icon: Cpu },
                { label: "Node.js Library", icon: Code2 },
                { label: "Webhooks Guide", icon: Zap }
              ].map((r, i) => (
                <div key={i} className="flex items-center justify-between text-slate-500 hover:text-blue-600 cursor-pointer transition-colors group">
                  <span className="text-xs font-bold flex items-center gap-2"><r.icon size={16} className="opacity-50" /> {r.label}</span>
                  <ChevronRight size={14} className="opacity-0 group-hover:opacity-100" />
                </div>
              ))}
            </div>
          </div>
          
          <div className="p-8 bg-emerald-50 rounded-[2rem] border border-emerald-100 text-emerald-800">
            <h4 className="text-[10px] font-black uppercase tracking-widest mb-2">Service Status</h4>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-xs font-bold">API Operational</span>
            </div>
            <p className="text-[10px] mt-4 font-bold opacity-70 italic text-emerald-600 leading-relaxed">
              Last Incident: 14 days ago (Scheduled Maintenance)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

import Link from "next/link";

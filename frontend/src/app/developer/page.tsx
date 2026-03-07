"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/services/api";
import { motion } from "framer-motion";
import { 
  Key, 
  Terminal, 
  BarChart3, 
  Copy, 
  Plus, 
  Trash2, 
  ExternalLink,
  Code2,
  Lock,
  Zap,
  Check
} from "lucide-react";
import { useState } from "react";

export default function DeveloperPortal() {
  const [copied, setCopied] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: keys, isLoading } = useQuery({
    queryKey: ["api-keys"],
    queryFn: async () => {
      const resp = await api.get("/developer/keys");
      return resp.data;
    }
  });

  const createKeyMutation = useMutation({
    mutationFn: async (label: string) => {
      const resp = await api.post("/developer/keys", { label });
      return resp.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    }
  });

  const deleteKeyMutation = useMutation({
    mutationFn: async (keyId: string) => {
      await api.delete(`/developer/keys/${keyId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    }
  });

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(text);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900">Developer Portal</h1>
          <p className="text-slate-400 font-bold text-sm uppercase tracking-widest mt-1">Integrate VisionDX AI into your own apps</p>
        </div>
        <div className="flex gap-3">
          <Link href="/developer/docs" className="bg-white border border-slate-100 flex items-center gap-2 px-6 py-3 rounded-2xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-all shadow-sm">
            <ExternalLink size={18} /> API Documentation
          </Link>
          <button 
            onClick={() => createKeyMutation.mutate("New App Key")}
            className="bg-blue-600 text-white px-8 py-3 rounded-2xl font-bold text-sm hover:bg-blue-700 transition-all shadow-xl shadow-blue-100 flex items-center gap-2"
          >
            <Plus size={18} /> Generate New Key
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* API Keys Section */}
          <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-8 border-b border-slate-50 flex items-center justify-between">
              <h2 className="text-xl font-black tracking-tight text-slate-900 flex items-center gap-2">
                <Lock size={20} className="text-blue-500" /> Active API Keys
              </h2>
            </div>
            
            <div className="p-4 space-y-2">
              {isLoading ? (
                <div className="p-8 space-y-4">
                  <div className="h-20 bg-slate-50 animate-pulse rounded-2xl" />
                  <div className="h-20 bg-slate-50 animate-pulse rounded-2xl" />
                </div>
              ) : keys?.length === 0 ? (
                <div className="p-16 text-center space-y-4">
                  <div className="w-16 h-16 bg-slate-50 rounded-3xl flex items-center justify-center mx-auto text-slate-300"><Key size={32} /></div>
                  <h3 className="font-bold text-slate-900">No keys generated yet</h3>
                  <p className="text-xs text-slate-400">Generate a key to start accessing our predictive models via REST API.</p>
                </div>
              ) : (
                keys.map((k: any) => (
                  <div key={k.id} className="p-6 rounded-2xl border border-slate-50 hover:border-blue-100 hover:bg-blue-50/20 transition-all group">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-black text-slate-900 uppercase tracking-widest">{k.label}</span>
                          <span className="text-[10px] bg-green-50 text-green-500 px-2 py-0.5 rounded-full font-black">ACTIVE</span>
                        </div>
                        <div className="flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-xl group-hover:bg-white transition-colors border border-transparent group-hover:border-blue-100">
                          <code className="text-xs text-slate-500 font-mono truncate">{k.api_key}</code>
                          <button 
                            onClick={() => handleCopy(k.api_key)}
                            className="ml-auto p-2 text-slate-300 hover:text-blue-600 transition-colors"
                          >
                            {copied === k.api_key ? <Check size={14} /> : <Copy size={14} />}
                          </button>
                        </div>
                      </div>
                      <button 
                        onClick={() => deleteKeyMutation.mutate(k.id)}
                        className="p-3 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Quick Start Code */}
          <div className="bg-slate-900 rounded-[2.5rem] p-8 text-white shadow-2xl overflow-hidden relative group">
            <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform"><Terminal size={120} /></div>
            <div className="flex items-center gap-3 mb-6">
              <Code2 size={24} className="text-blue-400" />
              <h3 className="text-xl font-black tracking-tight">Quick Integration</h3>
            </div>
            <pre className="bg-black/40 p-6 rounded-2xl text-[11px] font-mono leading-relaxed text-blue-100 overflow-x-auto border border-white/5">
{`curl -X POST "https://api.visiondx.ai/v1/analyze" \\
  -H "X-API-Key: YOUR_KEY_HERE" \\
  -H "Content-Type: application/json" \\
  -d '{
    "parameters": [
      {"name": "Hemoglobin", "value": 12.5, "unit": "g/dL"}
    ]
  }'`}
            </pre>
          </div>
        </div>

        <div className="space-y-8">
          {/* Usage Stats Panel */}
          <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm space-y-8">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">Global Usage</h3>
              <BarChart3 size={18} className="text-slate-100" />
            </div>
            
            <div className="space-y-6">
              {[
                { label: "API Requests", value: "2.4k", progress: 65, color: "bg-blue-500" },
                { label: "Prediction Calls", value: "840", progress: 40, color: "bg-indigo-500" },
                { label: "Rate Limit Info", value: "98%", progress: 98, color: "bg-emerald-500" },
              ].map((s, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between text-[10px] font-black uppercase tracking-tighter">
                    <span className="text-slate-500">{s.label}</span>
                    <span className="text-slate-900">{s.value}</span>
                  </div>
                  <div className="h-1.5 bg-slate-50 rounded-full overflow-hidden">
                    <motion.div 
                      className={`h-full ${s.color}`}
                      initial={{ width: 0 }}
                      animate={{ width: \`\${s.progress}%\` }}
                      transition={{ duration: 1, delay: i * 0.1 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pricing/Usage Panel */}
          <div className="bg-gradient-to-br from-blue-600 to-indigo-700 p-8 rounded-[2.5rem] text-white shadow-xl shadow-blue-100">
            <Zap className="mb-6 opacity-80" fill="currentColor" size={32} />
            <h3 className="text-lg font-black mb-2">Developer Free Tier</h3>
            <p className="text-[11px] text-blue-100 font-bold mb-6">You are currently using the community tier. 5,000 requests/mo included.</p>
            <button className="bg-white text-blue-700 px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-widest shadow-xl shadow-indigo-900/20 hover:scale-105 active:scale-95 transition-all w-full">
              Upgrade to Pro
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

import Link from "next/link";

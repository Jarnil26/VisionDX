"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowLeft, 
  FlaskConical, 
  AlertTriangle, 
  CheckCircle2, 
  TrendingUp, 
  TrendingDown,
  Info,
  Calendar,
  User,
  Zap,
  Download,
  Share2,
  Stethoscope,
  BrainCircuit,
  Activity
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function ReportDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"overview" | "abnormal" | "ai">("overview");

  const { data: report, isLoading: loadingReport } = useQuery({
    queryKey: ["report", id],
    queryFn: async () => {
      const resp = await api.get(`/report/${id}`);
      return resp.data;
    }
  });

  const { data: analysis, isLoading: loadingAnalysis } = useQuery({
    queryKey: ["analysis", id],
    queryFn: async () => {
      const resp = await api.get(`/report/${id}/analysis`);
      return resp.data;
    }
  });

  const { data: predictions, isLoading: loadingPredictions } = useQuery({
    queryKey: ["predictions", id],
    queryFn: async () => {
      const resp = await api.get(`/report/${id}/prediction`);
      return resp.data?.possible_conditions || [];
    }
  });

  if (loadingReport || loadingAnalysis) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-16 h-16 border-4 border-blue-50 border-t-blue-600 rounded-full animate-spin" />
        <p className="text-slate-400 font-bold text-sm uppercase tracking-widest animate-pulse">Running AI Diagnostic Suite...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in pb-20">
      {/* Action Header */}
      <div className="flex items-center justify-between">
        <button 
          onClick={() => router.back()}
          className="flex items-center gap-2 text-slate-400 hover:text-slate-900 font-bold text-sm transition-colors group"
        >
          <div className="p-2 rounded-xl group-hover:bg-slate-100 transition-all"><ArrowLeft size={18} /></div> Back to Records
        </button>
        <div className="flex gap-3">
          <button className="p-3 bg-white border border-slate-100 text-slate-500 rounded-xl hover:bg-slate-50 transition-all shadow-sm"><Share2 size={18} /></button>
          <button className="bg-slate-900 text-white px-6 py-3 rounded-xl font-bold text-sm hover:bg-slate-800 transition-all shadow-xl shadow-slate-200 flex items-center gap-2">
            <Download size={18} /> Export PDF
          </button>
        </div>
      </div>

      {/* Patient Profile Card */}
      <div className="bg-white rounded-[2.5rem] p-8 border border-slate-100 shadow-sm flex flex-col md:flex-row items-center gap-10">
        <div className="w-24 h-24 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-[2rem] flex items-center justify-center text-white text-3xl font-black shadow-2xl shadow-blue-100 shrink-0">
          {(report.patient_name || report.patient?.name || "?")[0]?.toUpperCase()}
        </div>
        <div className="text-center md:text-left flex-1">
          <div className="flex items-center justify-center md:justify-start gap-4 mb-2">
            <h1 className="text-2xl font-black tracking-tight text-slate-900">{report.patient_name || report.patient?.name || "Patient Profile"}</h1>
            <span className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-blue-100">
              Verified
            </span>
          </div>
          <div className="flex flex-wrap justify-center md:justify-start gap-6">
            <div className="flex items-center gap-2 text-slate-400 font-bold text-xs"><User size={14} className="opacity-50" /> {report.age || report.patient?.age || "-"} Years · {report.gender || report.patient?.gender || "-"}</div>
            <div className="flex items-center gap-2 text-slate-400 font-bold text-xs"><Calendar size={14} className="opacity-50" /> {new Date(report.created_at).toLocaleDateString()}</div>
            <div className="flex items-center gap-2 text-slate-400 font-bold text-xs"><FlaskConical size={14} className="opacity-50" /> {report.report_id}</div>
          </div>
        </div>
        <div className="hidden md:block h-12 w-[1px] bg-slate-100 mx-4"></div>
        <div className="flex gap-10">
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Status</p>
            <p className="text-sm font-black text-green-600 flex items-center gap-1.5"><CheckCircle2 size={14} /> Processed</p>
          </div>
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Lab Source</p>
            <p className="text-sm font-black text-slate-800">{report.lab_name || "VisionDX Core"}</p>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-4 gap-8 items-start">
        {/* Navigation Sidebar */}
        <div className="lg:col-span-1 space-y-4 sticky top-24">
          <button 
            onClick={() => setActiveTab("overview")}
            className={`w-full flex items-center gap-3 px-5 py-4 rounded-2xl text-sm font-bold transition-all ${activeTab === "overview" ? "bg-slate-900 text-white shadow-xl shadow-slate-200" : "bg-white text-slate-500 hover:bg-slate-50"}`}
          >
            <Activity size={18} /> Lab Markers
          </button>
          <button 
            onClick={() => setActiveTab("abnormal")}
            className={`w-full flex items-center gap-3 px-5 py-4 rounded-2xl text-sm font-bold transition-all ${activeTab === "abnormal" ? "bg-blue-600 text-white shadow-xl shadow-blue-100" : "bg-white text-slate-500 hover:bg-slate-50"}`}
          >
            <AlertTriangle size={18} /> Abnormal Analysis
          </button>
          <button 
            onClick={() => setActiveTab("ai")}
            className={`w-full flex items-center gap-3 px-5 py-4 rounded-2xl text-sm font-bold transition-all ${activeTab === "ai" ? "bg-indigo-600 text-white shadow-xl shadow-indigo-100" : "bg-white text-slate-500 hover:bg-slate-50"}`}
          >
            <Zap size={18} /> AI Predicton
          </button>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-3 space-y-8">
          <AnimatePresence mode="wait">
            {activeTab === "overview" && (
              <motion.div 
                key="overview"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-50/50">
                      <tr>
                        <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Biomarker</th>
                        <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Value</th>
                        <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Reference Range</th>
                        <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {report.parameters?.map((p: any, i: number) => (
                        <tr key={i} className={`group ${p.status !== "NORMAL" ? "bg-slate-50/30" : ""}`}>
                          <td className="px-8 py-5">
                            <p className="font-bold text-slate-800 text-sm">{p.name}</p>
                            <p className="text-[10px] text-slate-400 font-bold uppercase">{p.raw_name || "Detected"}</p>
                          </td>
                          <td className="px-8 py-5 text-center">
                            <span className={`text-lg font-black ${p.status === "HIGH" ? "text-red-500" : p.status === "LOW" ? "text-blue-500" : "text-slate-800"}`}>
                              {p.value}
                            </span>
                            <span className="text-[10px] text-slate-400 font-bold ml-1 uppercase">{p.unit}</span>
                          </td>
                          <td className="px-8 py-5">
                            <div className="flex flex-col gap-1">
                              <span className="text-xs font-bold text-slate-400 font-mono tracking-tighter bg-slate-100 px-2 py-0.5 rounded-lg inline-block w-fit">
                                {p.reference_range || "N/A"}
                              </span>
                            </div>
                          </td>
                          <td className="px-8 py-5">
                            {p.status === "HIGH" ? (
                              <span className="inline-flex items-center gap-1 text-[10px] font-black text-red-500 uppercase tracking-widest"><TrendingUp size={12} /> Elevated</span>
                            ) : p.status === "LOW" ? (
                              <span className="inline-flex items-center gap-1 text-[10px] font-black text-blue-500 uppercase tracking-widest"><TrendingDown size={12} /> Low</span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[10px] font-black text-green-500 uppercase tracking-widest"><CheckCircle2 size={12} /> Optimal</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {activeTab === "abnormal" && (
              <motion.div 
                key="abnormal"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                {/* Clinical Interpretation */}
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-[2.5rem] p-10 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-8 opacity-10"><BrainCircuit size={120} /></div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-200">
                      <Stethoscope size={20} />
                    </div>
                    <h3 className="text-xl font-black tracking-tight text-blue-900">Interpretation Summary</h3>
                  </div>
                  <p className="text-slate-700 font-medium leading-[1.8] text-lg italic">
                    "{analysis.summary}"
                  </p>
                </div>

                {/* Abnormal List */}
                <div className="grid gap-4">
                  {report.parameters?.filter((p: any) => p.status !== "NORMAL").map((p: any, i: number) => (
                    <div key={i} className={`p-6 rounded-[1.5rem] border flex items-center justify-between transition-all hover:scale-[1.01] ${p.status === "HIGH" ? "bg-red-50/50 border-red-100" : "bg-blue-50/50 border-blue-100"}`}>
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${p.status === "HIGH" ? "bg-red-500 text-white" : "bg-blue-500 text-white"}`}>
                          {p.status === "HIGH" ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                        </div>
                        <div>
                          <h4 className="font-black text-slate-900">{p.name}</h4>
                          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-0.5">Reference: {p.reference_range}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-2xl font-black ${p.status === "HIGH" ? "text-red-500" : "text-blue-500"}`}>{p.value} <span className="text-xs">{p.unit}</span></div>
                        <p className={`text-[10px] font-black uppercase tracking-widest ${p.status === "HIGH" ? "text-red-400" : "text-blue-400"}`}>{p.status === "HIGH" ? "Above Normal" : "Below Normal"}</p>
                      </div>
                    </div>
                  ))}
                  {(!report.parameters?.some((p: any) => p.status !== "NORMAL")) && (
                    <div className="bg-white rounded-[2.5rem] p-20 text-center space-y-4 border border-slate-100">
                      <div className="w-20 h-20 bg-green-50 text-green-500 rounded-3xl flex items-center justify-center mx-auto"><CheckCircle2 size={40} /></div>
                      <h3 className="text-xl font-black text-slate-900">Excellent Results</h3>
                      <p className="text-sm text-slate-400 font-bold max-w-xs mx-auto">All biomarkers are within the optimal clinical range.</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === "ai" && (
              <motion.div 
                key="ai"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-8"
              >
                <div className="bg-slate-900 text-white rounded-[2.5rem] p-10 relative overflow-hidden shadow-2xl">
                  <div className="absolute -right-20 -top-20 w-80 h-80 bg-blue-500/20 rounded-full blur-[100px]"></div>
                  <div className="flex items-center gap-3 mb-6 relative">
                    <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-900/40">
                      <Zap size={20} />
                    </div>
                    <h3 className="text-xl font-black tracking-tight">Disease Prediction Engine</h3>
                  </div>
                  <p className="text-slate-400 font-medium leading-relaxed max-w-xl relative">
                    VisionDX AI simulates thousands of medical scenarios based on your biomarkers to predict potential disease onset with high confidence scoring.
                  </p>
                </div>

                {loadingPredictions ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
                    {[1,2,3,4].map(i => <div key={i} className="h-40 bg-slate-100 rounded-3xl" />)}
                  </div>
                ) : predictions.length === 0 ? (
                  <div className="bg-white rounded-[2.5rem] p-20 text-center space-y-4 border border-slate-100">
                    <BrainCircuit className="mx-auto text-slate-200" size={48} />
                    <h3 className="text-xl font-black text-slate-900">No Significant Predictions</h3>
                    <p className="text-sm text-slate-400 font-bold max-w-xs mx-auto">Based on the current markers, the AI does not detect any secondary disease risks.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {predictions.map((p: any, i: number) => (
                      <div key={i} className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-sm relative group hover:shadow-xl hover:-translate-y-1 transition-all">
                        <div className="flex justify-between items-start mb-6">
                          <h4 className="text-lg font-black text-slate-900 group-hover:text-blue-600 transition-colors">{p.disease}</h4>
                          <span className={`px-4 py-2 rounded-xl text-lg font-black ${p.confidence >= 0.7 ? "bg-red-50 text-red-600" : "bg-blue-50 text-blue-600"}`}>
                            {Math.round(p.confidence * 100)}%
                          </span>
                        </div>
                        
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-8">
                          <motion.div 
                            className={`h-full rounded-full ${p.confidence >= 0.7 ? "bg-red-500" : "bg-blue-600"}`}
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.round(p.confidence * 100)}%` }}
                            transition={{ duration: 1, delay: i * 0.1 }}
                          />
                        </div>

                        <div className="flex items-center gap-2 text-slate-400 font-bold text-[10px] uppercase tracking-widest">
                          <Info size={12} /> Supporting Evidence Found in {report.parameters?.filter((param:any) => param.status !== "NORMAL").length} Markers
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="p-8 bg-amber-50 border border-amber-100 rounded-[2rem] flex gap-6 items-center">
                  <div className="w-14 h-14 bg-amber-200 text-amber-800 rounded-2xl flex items-center justify-center shrink-0 shadow-lg shadow-amber-200/50">
                    <AlertTriangle size={24} />
                  </div>
                  <div>
                    <h5 className="font-black text-amber-800 uppercase tracking-widest text-xs mb-1">Clinical Disclaimer</h5>
                    <p className="text-[11px] text-amber-700 font-bold leading-relaxed italic">
                      VisionDX is an AI-assisted tool meant for informational insights only. Predictions are probabilistic and should never replace a professional medical diagnosis. Consult your doctor for an official review of these findings.
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

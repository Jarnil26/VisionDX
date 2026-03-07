"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { motion } from "framer-motion";
import { 
  FileStack, 
  AlertTriangle, 
  FlaskConical, 
  CheckCircle2, 
  ArrowUpRight, 
  Clock,
  Zap
} from "lucide-react";
import Link from "next/link";

export default function PatientDashboard() {
  const { user } = useAuthStore();
  
  const { data: reports, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: async () => {
      const resp = await api.get("/reports?limit=5");
      return Array.isArray(resp.data) ? resp.data : resp.data.reports || [];
    }
  });

  const stats = [
    { label: "Total Reports", value: reports?.length || 0, icon: FileStack, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "Abnormalities", value: reports?.filter((r: any) => (r.abnormal_count || 0) > 0).length || 0, icon: AlertTriangle, color: "text-amber-600", bg: "bg-amber-50" },
    { label: "Tests Analyzed", value: reports?.reduce((acc: number, r: any) => acc + (r.total_parameters || 0), 0) || 0, icon: FlaskConical, color: "text-indigo-600", bg: "bg-indigo-50" },
    { label: "AI Predictions", value: reports?.filter((r: any) => (r.predictions?.length || 0) > 0).length || 0, icon: Zap, color: "text-purple-600", bg: "bg-purple-50" },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10 animate-fade-in">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white p-8 rounded-[2rem] border border-slate-100 shadow-sm">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900">
            Welcome back, <span className="text-blue-600">{user?.full_name?.split(" ")[0]}</span>
          </h1>
          <p className="text-slate-400 font-bold text-sm mt-1 uppercase tracking-widest">Your Health Intelligence Hub</p>
        </div>
        <div className="flex gap-3">
          <Link href="/reports/upload" className="bg-slate-900 text-white px-6 py-3 rounded-2xl font-bold text-sm hover:bg-slate-800 transition-all shadow-xl shadow-slate-200 flex items-center gap-2">
            <FileStack size={18} /> Upload Report
          </Link>
          <Link href="/chat" className="bg-blue-50 text-blue-600 border border-blue-100 px-6 py-3 rounded-2xl font-bold text-sm hover:bg-blue-100 transition-all flex items-center gap-2">
            <Zap size={18} /> AI Consultant
          </Link>
        </div>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group"
          >
            <div className={`w-12 h-12 ${stat.bg} ${stat.color} rounded-2xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110`}>
              <stat.icon size={22} />
            </div>
            <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">{stat.label}</p>
            <div className="flex items-end gap-2 mt-1">
              <span className="text-3xl font-black text-slate-900 leading-none">
                {isLoading ? "..." : stat.value}
              </span>
              <span className="text-[10px] text-green-500 font-bold mb-1">+12%</span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Recent Reports List */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between px-2">
            <h2 className="text-xl font-black tracking-tight text-slate-900">Recent Health Reports</h2>
            <Link href="/reports" className="text-xs font-bold text-blue-600 hover:underline">View All History</Link>
          </div>
          
          <div className="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden">
            {isLoading ? (
              <div className="p-8 space-y-4">
                {[1,2,3].map(i => <div key={i} className="h-16 bg-slate-50 animate-pulse rounded-2xl" />)}
              </div>
            ) : reports?.length === 0 ? (
              <div className="p-16 text-center space-y-4">
                <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto">
                  <FileStack className="text-slate-300" size={32} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900">No reports found</h3>
                  <p className="text-xs text-slate-400 mt-1">Upload your first lab report to get AI insights.</p>
                </div>
                <Link href="/reports/upload" className="inline-block bg-blue-600 text-white px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-widest shadow-lg shadow-blue-100">Click to Upload</Link>
              </div>
            ) : (
              <div className="divide-y divide-slate-50">
                {reports?.map((report: any) => (
                  <Link 
                    key={report.report_id} 
                    href={`/reports/${report.report_id}`}
                    className="flex p-6 items-center gap-6 hover:bg-slate-50 transition-colors group"
                  >
                    <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center text-slate-400 font-black text-sm group-hover:bg-blue-600 group-hover:text-white transition-all">
                      PDF
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-slate-900">{report.patient_name || "Diagnostic Report"}</h4>
                        <span className="text-[10px] bg-slate-100 text-slate-500 font-black px-2 py-0.5 rounded-full">{report.report_id}</span>
                      </div>
                      <div className="flex items-center gap-4 mt-1">
                        <span className="text-xs text-slate-400 flex items-center gap-1"><Clock size={12} /> {new Date(report.created_at).toLocaleDateString()}</span>
                        <span className="text-xs text-slate-400 flex items-center gap-1"><FlaskConical size={12} /> {report.total_parameters || 0} Markers</span>
                      </div>
                    </div>
                    <div className="text-right">
                      {(report.abnormal_count || 0) > 0 ? (
                        <div className="bg-amber-50 text-amber-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-amber-100">
                          {report.abnormal_count} Alerts
                        </div>
                      ) : (
                        <div className="bg-green-50 text-green-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-green-100">
                          Normal
                        </div>
                      )}
                      <div className="mt-2 text-slate-300 group-hover:text-blue-600 transition-colors">
                        <ArrowUpRight size={18} />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Insights */}
        <div className="space-y-6">
          <h2 className="text-xl font-black tracking-tight text-slate-900 px-2">Clinical Insights</h2>
          
          <div className="bg-gradient-to-br from-indigo-600 to-blue-700 rounded-[2rem] p-8 text-white shadow-xl shadow-blue-100 relative overflow-hidden group">
            <div className="absolute -right-8 -bottom-8 w-40 h-40 bg-white/10 rounded-full blur-3xl transition-transform group-hover:scale-150"></div>
            <Zap className="mb-6 opacity-80" fill="currentColor" size={32} />
            <h3 className="text-lg font-black mb-3 leading-tight">AI Predicted Risk: High Vitamin D Deficiency</h3>
            <p className="text-xs text-blue-100 font-medium leading-relaxed mb-6">
              Based on your latest 3 reports, we've noticed a declining trend in Vitamin D levels. We recommend a consultation soon.
            </p>
            <button className="bg-white text-blue-700 px-5 py-3 rounded-xl font-bold text-xs uppercase tracking-widest shadow-xl shadow-indigo-900/20 hover:scale-105 active:scale-95 transition-all">
              See Full Prediction
            </button>
          </div>

          <div className="bg-white rounded-[2rem] border border-slate-100 shadow-sm p-8 space-y-6">
            <div className="flex items-center gap-2 text-emerald-600">
              <CheckCircle2 size={18} />
              <span className="text-xs font-black uppercase tracking-[0.1em]">On Track</span>
            </div>
            <h3 className="font-black text-slate-900">Weekly Wellness Check</h3>
            <p className="text-xs text-slate-400 font-medium leading-relaxed">
              You've completed your followups for 3 weeks consecutively. Keep it up for a monthly health reward!
            </p>
            <Link href="/followups" className="block w-full text-center py-4 rounded-2xl border border-slate-200 text-slate-600 font-bold text-sm hover:bg-slate-50 transition-all">
              Update Today's Status
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import { motion } from "framer-motion";
import { 
  Search, 
  Filter, 
  FileText, 
  ChevronRight, 
  Calendar, 
  AlertCircle,
  Clock,
  ExternalLink,
  Loader2,
  CheckCircle2
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function ReportsHistoryPage() {
  const [search, setSearch] = useState("");
  
  const { data: reports, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: async () => {
      const resp = await api.get("/reports");
      return Array.isArray(resp.data) ? resp.data : resp.data.reports || [];
    }
  });

  const filteredReports = reports?.filter((r: any) => 
    r.patient_name?.toLowerCase().includes(search.toLowerCase()) ||
    r.report_id?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900">Medical History</h1>
          <p className="text-slate-400 font-bold text-sm uppercase tracking-widest mt-1">Archive of all AI analyzed reports</p>
        </div>
        <Link href="/reports/upload" className="bg-blue-600 text-white px-8 py-3 rounded-2xl font-bold text-sm hover:bg-blue-700 transition-all shadow-xl shadow-blue-100 flex items-center gap-2">
          New Analysis
        </Link>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1 group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18} />
          <input 
            type="text" 
            placeholder="Search by patient name or report ID..."
            className="w-full pl-12 pr-4 py-4 bg-white border border-slate-100 rounded-2xl text-sm font-medium focus:outline-none focus:ring-4 focus:ring-blue-50/50 focus:border-blue-200 shadow-sm transition-all"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button className="flex items-center gap-2 px-6 py-4 bg-white border border-slate-100 rounded-2xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-all shadow-sm">
          <Filter size={18} /> Filter List
        </button>
      </div>

      {/* Results Table/List */}
      <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-20 flex flex-col items-center justify-center gap-4">
            <Loader2 className="animate-spin text-blue-500" size={40} />
            <p className="text-slate-400 font-bold text-sm uppercase tracking-widest">Accessing records...</p>
          </div>
        ) : filteredReports?.length === 0 ? (
          <div className="p-20 text-center space-y-4">
            <div className="w-20 h-20 bg-slate-50 rounded-3xl flex items-center justify-center mx-auto text-slate-300">
              <FileText size={40} />
            </div>
            <h3 className="text-lg font-black text-slate-900">No matching records</h3>
            <p className="text-sm text-slate-400 max-w-xs mx-auto">Try adjusting your search or upload a new report to get started.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Diagnostic Report</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Stats</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Risk Level</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Date Processed</th>
                  <th className="px-8 py-5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filteredReports?.map((report: any, i: number) => (
                  <motion.tr 
                    key={report.report_id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="group hover:bg-blue-50/30 transition-colors"
                  >
                    <td className="px-8 py-6">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center text-slate-400 font-black group-hover:bg-blue-600 group-hover:text-white transition-all text-sm">
                          {report.patient_name?.[0] || "?"}
                        </div>
                        <div>
                          <p className="font-black text-slate-900 leading-none">{report.patient_name || "Unknown Patient"}</p>
                          <p className="text-[10px] font-bold text-slate-400 mt-1 uppercase tracking-tighter">{report.report_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="flex items-center gap-6">
                        <div className="space-y-1">
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">Markers</p>
                          <p className="text-sm font-black text-slate-800">{report.total_parameters || 0}</p>
                        </div>
                        <div className="space-y-1">
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">AI Alerts</p>
                          <p className={`text-sm font-black ${(report.abnormal_count || 0) > 0 ? "text-amber-500" : "text-green-500"}`}>
                            {report.abnormal_count || 0}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      {(report.abnormal_count || 0) > 3 ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-50 text-red-600 rounded-full text-[10px] font-black uppercase tracking-widest border border-red-100">
                          <AlertCircle size={12} /> High Risk
                        </span>
                      ) : (report.abnormal_count || 0) > 0 ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 text-amber-600 rounded-full text-[10px] font-black uppercase tracking-widest border border-amber-100">
                          <Clock size={12} /> Moderate
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-50 text-green-600 rounded-full text-[10px] font-black uppercase tracking-widest border border-green-100">
                          <CheckCircle2 size={12} /> Optimal
                        </span>
                      )}
                    </td>
                    <td className="px-8 py-6">
                      <div className="flex items-center gap-2 text-slate-500 font-bold text-sm">
                        <Calendar size={14} className="opacity-50" />
                        {new Date(report.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-8 py-6 text-right">
                      <Link 
                        href={`/reports/${report.report_id}`}
                        className="p-3 bg-white border border-slate-100 rounded-xl text-slate-400 hover:text-blue-600 hover:border-blue-200 hover:shadow-lg transition-all inline-block"
                      >
                        <ChevronRight size={20} />
                      </Link>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

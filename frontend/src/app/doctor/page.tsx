"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import { motion } from "framer-motion";
import { 
  Users, 
  AlertTriangle, 
  Search, 
  ChevronRight, 
  Filter,
  Activity,
  UserCheck,
  Stethoscope,
  Clock,
  ExternalLink
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function DoctorDashboard() {
  const [search, setSearch] = useState("");

  const { data: patients, isLoading: loadingPatients } = useQuery({
    queryKey: ["doctor-patients"],
    queryFn: async () => {
      // For doctor, we might have a dedicated endpoint /doctor/patients or similar
      // For now, let's use /reports and group by patient
      const resp = await api.get("/reports?all=true");
      const reports = Array.isArray(resp.data) ? resp.data : resp.data.reports || [];
      
      // Primitive grouping for demo
      const grouped: any = {};
      reports.forEach((r: any) => {
        if (!grouped[r.patient_name]) {
          grouped[r.patient_name] = { 
            name: r.patient_name, 
            reports: 0, 
            alerts: 0, 
            latest: r.created_at,
            risk: "Low"
          };
        }
        grouped[r.patient_name].reports += 1;
        grouped[r.patient_name].alerts += (r.abnormal_count || 0);
        if (new Date(r.created_at) > new Date(grouped[r.patient_name].latest)) {
          grouped[r.patient_name].latest = r.created_at;
        }
      });

      return Object.values(grouped).map((p: any) => ({
        ...p,
        risk: p.alerts > 10 ? "Critical" : p.alerts > 3 ? "Moderate" : "Low"
      })).sort((a: any, b: any) => (b.alerts - a.alerts));
    }
  });

  const stats = [
    { label: "Total Patients", value: patients?.length || 0, icon: Users, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "High Risk Alerts", value: patients?.filter((p: any) => p.risk === "Critical").length || 0, icon: AlertTriangle, color: "text-red-600", bg: "bg-red-50" },
    { label: "Reviewed Today", value: "18", icon: UserCheck, color: "text-emerald-600", bg: "bg-emerald-50" },
    { label: "Pending Tests", value: "4", icon: Clock, color: "text-amber-600", bg: "bg-amber-50" },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900">Clinical Surveillance</h1>
          <p className="text-slate-400 font-bold text-sm uppercase tracking-widest mt-1">Monitoring abnormal patient trends</p>
        </div>
        <div className="flex gap-3">
          <button className="bg-white border border-slate-100 flex items-center gap-2 px-6 py-3 rounded-2xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-all shadow-sm">
            <Filter size={18} /> Filters
          </button>
          <button className="bg-slate-900 text-white px-8 py-3 rounded-2xl font-bold text-sm hover:bg-slate-800 transition-all shadow-xl shadow-slate-200">
            Export Clinical Report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
            <div className={`w-12 h-12 ${stat.bg} ${stat.color} rounded-2xl flex items-center justify-center mb-4`}>
              <stat.icon size={22} />
            </div>
            <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest leading-none mb-2">{stat.label}</p>
            <h3 className="text-3xl font-black text-slate-900 tracking-tighter">{stat.value}</h3>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-8 border-b border-slate-50 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <h2 className="text-xl font-black tracking-tight text-slate-900">Patient Risk Queue</h2>
          <div className="relative w-full md:w-80 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={16} />
            <input 
              type="text" 
              placeholder="Search patients..."
              className="w-full pl-10 pr-4 py-3 bg-slate-50 border-none rounded-xl text-xs font-bold focus:ring-2 focus:ring-blue-100 outline-none transition-all"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50">
                <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Patient Identity</th>
                <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Alert Count</th>
                <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Risk Category</th>
                <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Last Update</th>
                <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {loadingPatients ? (
                Array(5).fill(0).map((_, i) => (
                  <tr key={i}><td colSpan={5} className="px-8 py-4"><div className="h-8 bg-slate-50 animate-pulse rounded-lg" /></td></tr>
                ))
              ) : patients?.map((p: any, i: number) => (
                <tr key={i} className="group hover:bg-slate-50/50 transition-colors">
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center text-slate-400 font-bold text-xs uppercase group-hover:bg-blue-600 group-hover:text-white transition-all">
                        {p.name?.[0]}
                      </div>
                      <p className="font-black text-slate-800 text-sm tracking-tight">{p.name || "Anonymous"}</p>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-center">
                    <span className={`text-sm font-black ${p.alerts > 0 ? "text-amber-500" : "text-slate-400"}`}>{p.alerts} Flagged</span>
                  </td>
                  <td className="px-8 py-6">
                    {p.risk === "Critical" ? (
                      <span className="bg-red-50 text-red-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-red-100 animate-pulse">Critical</span>
                    ) : p.risk === "Moderate" ? (
                      <span className="bg-amber-50 text-amber-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-amber-100">Action Required</span>
                    ) : (
                      <span className="bg-green-50 text-green-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-green-100">Stable</span>
                    )}
                  </td>
                  <td className="px-8 py-6">
                    <p className="text-xs text-slate-400 font-bold">{new Date(p.latest).toLocaleDateString()}</p>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <button className="text-slate-400 hover:text-blue-600 p-2 transition-all"><ExternalLink size={18} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

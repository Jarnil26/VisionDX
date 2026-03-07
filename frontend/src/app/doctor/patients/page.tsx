"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import { motion } from "framer-motion";
import { 
  Users, 
  Search, 
  FileText, 
  ChevronRight,
  ExternalLink,
  Filter
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function PatientArchivePage() {
  const [search, setSearch] = useState("");

  const { data: patients, isLoading } = useQuery({
    queryKey: ["archive-patients"],
    queryFn: async () => {
      const resp = await api.get("/reports?all=true");
      const reports = Array.isArray(resp.data) ? resp.data : resp.data.reports || [];
      const grouped: any = {};
      reports.forEach((r: any) => {
        if (!grouped[r.patient_name]) grouped[r.patient_name] = { name: r.patient_name, reports: 0 };
        grouped[r.patient_name].reports++;
      });
      return Object.values(grouped);
    }
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10 animate-fade-in">
      <div className="space-y-2">
        <h1 className="text-3xl font-black tracking-tight text-slate-900">Patient Archive</h1>
        <p className="text-slate-400 font-bold text-sm uppercase tracking-widest">Historical clinical records</p>
      </div>

      <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden p-8">
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18} />
            <input 
              type="text" 
              placeholder="Search by name..."
              className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-2xl text-sm font-bold focus:ring-4 focus:ring-blue-50 outline-none transition-all"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button className="px-8 py-4 bg-white border border-slate-100 rounded-2xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-all flex items-center gap-2">
            <Filter size={18} /> Filter Records
          </button>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
             Array(6).fill(0).map((_, i) => <div key={i} className="h-24 bg-slate-50 animate-pulse rounded-2xl" />)
          ) : patients?.map((p: any, i: number) => (
            <div key={i} className="p-6 rounded-2xl border border-slate-50 hover:border-blue-100 hover:bg-blue-50/20 transition-all group flex items-center justify-between">
               <div className="flex items-center gap-4">
                 <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center text-slate-400 font-black group-hover:bg-blue-600 group-hover:text-white transition-all">
                    {p.name?.[0]}
                 </div>
                 <div>
                   <h3 className="font-bold text-slate-800 text-sm">{p.name}</h3>
                   <p className="text-[10px] text-slate-400 font-black uppercase tracking-tighter">{p.reports} Historical Reports</p>
                 </div>
               </div>
               <button className="p-2 text-slate-300 hover:text-blue-600 transition-colors"><ChevronRight size={20} /></button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

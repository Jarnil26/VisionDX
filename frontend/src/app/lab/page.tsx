"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import { motion } from "framer-motion";
import { 
  ClipboardList, 
  FlaskConical, 
  CheckCircle2, 
  Clock, 
  User, 
  ArrowUpRight,
  MoreVertical,
  Calendar,
  Search
} from "lucide-react";
import Link from "next/link";

export default function LabDashboard() {
  const { data: bookings, isLoading } = useQuery({
    queryKey: ["lab-bookings"],
    queryFn: async () => {
      // Mock or fetch bookings
      return [
        { id: "BOK-9021", patient: "Alice Smith", test: "Complete Blood Count", date: "2026-03-08", status: "Pending", time: "09:00 AM" },
        { id: "BOK-9022", patient: "Bob Johnson", test: "Thyroid Profile", date: "2026-03-08", status: "Sample Collected", time: "10:30 AM" },
        { id: "BOK-9023", patient: "Charlie Brown", test: "Lipid Profile", date: "2026-03-08", status: "In Analysis", time: "11:15 AM" },
        { id: "BOK-9024", patient: "David Miller", test: "Vitamin D", date: "2026-03-09", status: "Confirmed", time: "08:15 AM" },
      ];
    }
  });

  const stats = [
    { label: "Pending Samples", value: "12", icon: FlaskConical, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "Today's Bookings", value: "34", icon: Calendar, color: "text-indigo-600", bg: "bg-indigo-50" },
    { label: "Results Ready", value: "8", icon: CheckCircle2, color: "text-green-600", bg: "bg-green-50" },
    { label: "Delayed Analysis", value: "2", icon: Clock, color: "text-red-500", bg: "bg-red-50" },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900">Lab Operations</h1>
          <p className="text-slate-400 font-bold text-sm uppercase tracking-widest mt-1">Diagnostic queue & Sample Tracking</p>
        </div>
        <Link href="/reports/upload" className="bg-slate-900 text-white px-8 py-3 rounded-2xl font-bold text-sm hover:bg-slate-800 transition-all shadow-xl shadow-slate-200 flex items-center gap-2">
          Process Lab Result
        </Link>
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
          <h2 className="text-xl font-black tracking-tight text-slate-900">Appointment Queue</h2>
          <div className="relative w-full md:w-80 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={16} />
            <input 
              type="text" 
              placeholder="Search by ID or Patient..."
              className="w-full pl-10 pr-4 py-3 bg-slate-50 border-none rounded-xl text-xs font-bold focus:ring-2 focus:ring-blue-100 outline-none transition-all"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50">
                <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Patient & Test</th>
                <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Schedule</th>
                <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Operation Status</th>
                <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {isLoading ? (
                Array(4).fill(0).map((_, i) => <tr key={i}><td colSpan={4} className="px-8 py-4"><div className="h-10 bg-slate-50 animate-pulse rounded-lg" /></td></tr>)
              ) : bookings?.map((b, i) => (
                <tr key={i} className="group hover:bg-slate-50/50 transition-colors">
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center text-slate-400 font-black group-hover:bg-blue-600 group-hover:text-white transition-all">
                        <User size={18} />
                      </div>
                      <div>
                        <p className="font-black text-slate-800 text-sm">{b.patient}</p>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">{b.test} · {b.id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-center">
                    <div className="inline-block text-left">
                      <p className="text-xs font-black text-slate-800">{b.date}</p>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">{b.time}</p>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${
                      b.status === "Pending" ? "bg-amber-50 text-amber-600 border-amber-100" :
                      b.status === "Sample Collected" ? "bg-blue-50 text-blue-600 border-blue-100" :
                      b.status === "In Analysis" ? "bg-indigo-50 text-indigo-600 border-indigo-100" :
                      "bg-slate-50 text-slate-500 border-slate-100"
                    }`}>
                      {b.status === "In Analysis" && <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse"></span>}
                      {b.status}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button className="p-2 text-slate-400 hover:text-blue-600 transition-all"><MoreVertical size={18} /></button>
                      <button className="p-2 bg-slate-50 text-slate-800 rounded-xl hover:bg-slate-100 transition-all"><ArrowUpRight size={18} /></button>
                    </div>
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

"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import { motion } from "framer-motion";
import { 
  MapPin, 
  Star, 
  FlaskConical, 
  ChevronRight, 
  Search, 
  Filter,
  ShieldCheck,
  Zap,
  Clock
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function LabsPage() {
  const [search, setSearch] = useState("");

  const labs = [
    { id: "L-101", name: "Modern Diagnostics Center", location: "Andheri West, Mumbai", rating: 4.8, reviews: 1200, tests: ["CBC", "Lipid", "Thyroid"], image: "🔬" },
    { id: "L-102", name: "HealthPlus Lab", location: "Koramangala, Bangalore", rating: 4.9, reviews: 850, tests: ["Vitamin D", "Diabetes", "Kidney"], image: "🧪" },
    { id: "L-103", name: "Precision Path Labs", location: "Hitech City, Hyderabad", rating: 4.7, reviews: 2400, tests: ["Full Body", "Allergy", "COVID"], image: "🧬" },
    { id: "L-104", name: "Metro Scan & Labs", location: "Connaught Place, Delhi", rating: 4.6, reviews: 1800, tests: ["Liver", "MRI", "Blood"], image: "💉" },
  ];

  const filteredLabs = labs.filter(l => l.name.toLowerCase().includes(search.toLowerCase()) || l.location.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10 animate-fade-in pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900">Partner Diagnostics</h1>
          <p className="text-slate-400 font-bold text-sm uppercase tracking-widest mt-1">Discover certified labs with VisionDX integration</p>
        </div>
        <div className="flex gap-4 p-1 bg-white border border-slate-100 rounded-2xl shadow-sm">
          <button className="px-6 py-2 bg-slate-900 text-white rounded-xl text-xs font-black uppercase tracking-widest">List View</button>
          <button className="px-6 py-2 text-slate-400 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-slate-50">Map View</button>
        </div>
      </div>

      {/* Search & Stats */}
      <div className="grid lg:grid-cols-4 gap-8">
        <div className="lg:col-span-3 space-y-8">
          <div className="flex gap-4">
            <div className="relative flex-1 group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18} />
              <input 
                type="text" 
                placeholder="Search by lab name, location, or test type..."
                className="w-full pl-12 pr-4 py-4 bg-white border border-slate-100 rounded-2xl text-sm font-medium focus:outline-none focus:ring-4 focus:ring-blue-50/50 focus:border-blue-200 shadow-sm transition-all"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button className="flex items-center gap-2 px-6 py-4 bg-white border border-slate-100 rounded-2xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-all shadow-sm">
              <Filter size={18} /> Filters
            </button>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {filteredLabs.map((lab, i) => (
              <motion.div 
                key={lab.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-white rounded-[2rem] p-8 border border-slate-50 shadow-sm hover:shadow-xl hover:border-blue-100 transition-all group"
              >
                <div className="flex justify-between items-start mb-6">
                  <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center text-3xl group-hover:scale-110 transition-transform">
                    {lab.image}
                  </div>
                  <div className="bg-emerald-50 text-emerald-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest flex items-center gap-1">
                    <ShieldCheck size={12} /> Partner Lab
                  </div>
                </div>

                <h3 className="text-xl font-black text-slate-900 group-hover:text-blue-600 transition-colors mb-2 tracking-tight">
                  {lab.name}
                </h3>
                
                <div className="flex items-center gap-2 text-slate-400 font-bold text-xs mb-6">
                  <MapPin size={14} className="text-red-400" /> {lab.location}
                </div>

                <div className="flex items-center gap-6 mb-8 border-y border-slate-50 py-4">
                  <div className="flex items-center gap-1 border-r border-slate-50 pr-6">
                    <Star className="text-amber-400 fill-amber-400" size={14} />
                    <span className="text-sm font-black text-slate-800">{lab.rating}</span>
                    <span className="text-[10px] text-slate-300 font-bold">({lab.reviews})</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Zap size={14} className="text-blue-500" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">AI results in 2h</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex gap-2">
                    {lab.tests.map(t => (
                      <span key={t} className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
                        {t}
                      </span>
                    ))}
                  </div>
                  <Link 
                    href={`/labs/book?lab=${lab.id}`}
                    className="p-4 bg-slate-900 text-white rounded-2xl hover:bg-slate-800 transition-all shadow-xl shadow-slate-200"
                  >
                    <ChevronRight size={20} />
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-gradient-to-br from-indigo-600 to-blue-700 p-8 rounded-[2rem] text-white shadow-xl shadow-blue-100 relative overflow-hidden group">
            <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-white/10 rounded-full blur-[80px] group-hover:scale-125 transition-transform"></div>
            <h3 className="text-lg font-black mb-4 relative">AI Home Collection</h3>
            <p className="text-xs text-blue-100 font-medium leading-[1.8] mb-8 relative">
              Book a sample collection at your doorstep. Results verified and analyzed by VisionDX AI within 4 hours.
            </p>
            <button className="relative w-full py-4 bg-white text-blue-700 rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl shadow-blue-900/20 hover:scale-[1.02] transition-all">
              Schedule Collection
            </button>
          </div>

          <div className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-sm space-y-6">
            <h4 className="text-[10px] font-black text-slate-900 uppercase tracking-[0.2em] border-b border-slate-50 pb-4">Why Book with Us?</h4>
            <div className="space-y-6">
              {[
                { icon: Clock, title: "No Queues", desc: "Priority slots for VisionDX users", color: "text-amber-500" },
                { icon: Zap, title: "AI Reports", desc: "Instant predictive diagnosis", color: "text-blue-500" },
                { icon: ShieldCheck, title: "Verified Labs", desc: "Strict quality compliance", color: "text-emerald-500" }
              ].map((item, i) => (
                <div key={i} className="flex gap-4">
                  <div className={`w-10 h-10 bg-slate-50 ${item.color} rounded-xl flex items-center justify-center shrink-0`}>
                    <item.icon size={18} />
                  </div>
                  <div>
                    <h5 className="text-[11px] font-black text-slate-800 border-none">{item.title}</h5>
                    <p className="text-[10px] text-slate-400 font-bold mt-0.5">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  Heart, 
  Smile, 
  Frown, 
  Meh, 
  Utensils, 
  Zap, 
  Moon, 
  CheckCircle2,
  Stethoscope,
  Info
} from "lucide-react";
import Link from "next/link";

export default function FollowupPage() {
  const [submitted, setSubmitted] = useState(false);
  const [data, setData] = useState({
    mood: "good",
    energy: 5,
    sleep: 7,
    symptoms: [] as string[],
  });

  const symptoms = ["Headache", "Fatigue", "Nausea", "Joint Pain", "Dizziness"];

  const handleToggleSymptom = (s: string) => {
    setData(prev => ({
      ...prev,
      symptoms: prev.symptoms.includes(s) 
        ? prev.symptoms.filter(x => x !== s) 
        : [...prev.symptoms, s]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="p-8 max-w-2xl mx-auto space-y-10 animate-fade-in py-20">
        <div className="bg-white rounded-[2.5rem] p-16 text-center shadow-sm border border-slate-100 space-y-8">
          <div className="w-24 h-24 bg-blue-50 text-blue-600 rounded-3xl flex items-center justify-center mx-auto shadow-lg shadow-blue-100">
            <CheckCircle2 size={48} />
          </div>
          <div>
            <h2 className="text-3xl font-black text-slate-900 tracking-tight">Health Status Updated</h2>
            <p className="text-slate-400 font-bold text-sm mt-3 uppercase tracking-widest leading-relaxed">
              We've synced your daily feedback with our AI analysis engine.
            </p>
          </div>
          <div className="p-6 bg-indigo-50 rounded-2xl border border-indigo-100 flex items-center gap-4 text-left">
            <Zap className="text-indigo-600 shrink-0" size={24} />
            <p className="text-[11px] text-indigo-700 font-bold italic">
              "Based on your report trends, your energy levels are expected to stabilize by Thursday. Keep up the consistent sleep schedule!"
            </p>
          </div>
          <Link href="/dashboard" className="inline-block bg-slate-900 text-white px-10 py-4 rounded-2xl font-black text-sm hover:bg-slate-800 transition-all shadow-xl shadow-slate-200">
            Go to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-10 animate-fade-in pb-20">
      <div>
        <h1 className="text-3xl font-black tracking-tight text-slate-900 text-center">Daily Wellness Check</h1>
        <p className="text-slate-400 font-bold text-sm uppercase tracking-widest mt-2 text-center">Help our AI understand your progress</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-sm space-y-12">
        {/* Mood */}
        <div className="space-y-6">
          <label className="text-xs font-black text-slate-900 uppercase tracking-widest text-center block">How are you feeling today?</label>
          <div className="flex justify-center gap-6">
            {[
              { id: "bad", icon: Frown, color: "text-red-500", bg: "bg-red-50" },
              { id: "okay", icon: Meh, color: "text-amber-500", bg: "bg-amber-50" },
              { id: "good", icon: Smile, color: "text-green-500", bg: "bg-green-50" },
            ].map(m => (
              <button 
                key={m.id}
                type="button"
                onClick={() => setData({ ...data, mood: m.id })}
                className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all ${data.mood === m.id ? `${m.bg} ${m.color} shadow-lg scale-110 border-2 border-transparent` : "bg-slate-50 text-slate-400 hover:bg-slate-100"}`}
              >
                <m.icon size={32} />
              </button>
            ))}
          </div>
        </div>

        {/* Energy Range */}
        <div className="space-y-6">
          <div className="flex justify-between items-end">
            <label className="text-xs font-black text-slate-900 uppercase tracking-widest">Energy Level</label>
            <span className="text-2xl font-black text-blue-600">{data.energy}/10</span>
          </div>
          <input 
            type="range" min="1" max="10" 
            className="w-full h-3 bg-slate-100 rounded-full appearance-none cursor-pointer accent-blue-600"
            value={data.energy}
            onChange={(e) => setData({ ...data, energy: parseInt(e.target.value) })}
          />
          <div className="flex justify-between text-[10px] font-black text-slate-300 uppercase tracking-tighter">
            <span>Low Battery</span>
            <span>Fully Charged</span>
          </div>
        </div>

        {/* Symptoms */}
        <div className="space-y-6">
          <label className="text-xs font-black text-slate-900 uppercase tracking-widest block">Are you experiencing any of these?</label>
          <div className="flex flex-wrap gap-3">
            {symptoms.map(s => (
              <button 
                key={s}
                type="button"
                onClick={() => handleToggleSymptom(s)}
                className={`px-6 py-3 rounded-xl text-xs font-bold transition-all border ${data.symptoms.includes(s) ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-500 border-slate-100 hover:border-slate-200"}`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Info Box */}
        <div className="p-6 bg-blue-50 rounded-2xl border border-blue-100 flex gap-4">
          <Info className="text-blue-500 shrink-0" size={20} />
          <p className="text-[10px] text-blue-700 font-bold leading-relaxed italic">
            This data is cross-referenced with your blood markers to detect early warning signs of chronic conditions or recovery bottlenecks.
          </p>
        </div>

        <button 
          type="submit"
          className="w-full py-5 bg-blue-600 text-white rounded-2xl font-black text-lg shadow-2xl shadow-blue-100 hover:bg-blue-700 hover:-translate-y-1 transition-all"
        >
          Submit Daily Check-in
        </button>
      </form>
    </div>
  );
}

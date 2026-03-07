"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { 
  Calendar, 
  MapPin, 
  CheckCircle2, 
  ChevronRight, 
  ArrowLeft,
  Clock,
  ShieldCheck,
  FlaskConical,
  CreditCard
} from "lucide-react";
import Link from "next/link";

export default function BookLabPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const labId = searchParams.get("lab");
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const [bookingData, setBookingData] = useState({
    testType: "Complete Blood Count (CBC)",
    date: "",
    time: "",
    homeCollection: false,
  });

  const handleBooking = async () => {
    setLoading(true);
    // Mock booking process
    setTimeout(() => {
      setLoading(false);
      setStep(3);
    }, 2000);
  };

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-10 animate-fade-in pb-20">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="p-2 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-all">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">Schedule Diagnostic Test</h1>
      </div>

      {/* Progress Stepper */}
      <div className="flex items-center justify-between px-4">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-black text-sm transition-all ${step >= s ? "bg-blue-600 text-white shadow-lg shadow-blue-100" : "bg-slate-100 text-slate-400"}`}>
              {step > s ? <CheckCircle2 size={18} /> : s}
            </div>
            {s < 3 && <div className={`w-16 h-[2px] rounded-full ${step > s ? "bg-blue-600" : "bg-slate-100"}`} />}
          </div>
        ))}
      </div>

      <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden">
        {step === 1 && (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="p-10 space-y-8">
            <div className="space-y-6">
              <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">Select Diagnostic Package</h3>
              <div className="grid gap-3">
                {["Complete Blood Count (CBC)", "Full Thyroid Profile", "Lipid & Sugar Screening", "Diabetes Monitoring (HbA1c)"].map((t) => (
                  <label key={t} className={`flex items-center justify-between p-5 rounded-2xl border-2 cursor-pointer transition-all ${bookingData.testType === t ? "border-blue-500 bg-blue-50/30 shadow-sm" : "border-slate-50 hover:border-slate-100 hover:bg-slate-50"}`}>
                    <div className="flex items-center gap-4">
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${bookingData.testType === t ? "border-blue-500 bg-blue-500" : "border-slate-200"}`}>
                        {bookingData.testType === t && <div className="w-2 h-2 bg-white rounded-full" />}
                      </div>
                      <span className="font-bold text-slate-700">{t}</span>
                    </div>
                    <input type="radio" className="hidden" value={t} checked={bookingData.testType === t} onChange={() => setBookingData({ ...bookingData, testType: t })} />
                    <span className="text-xs font-black text-blue-600">$45.00</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between pt-6 border-t border-slate-50">
              <div className="flex items-center gap-2 text-slate-400 text-xs font-bold uppercase">
                <ShieldCheck size={16} className="text-blue-500" /> Secure Checkout
              </div>
              <button 
                onClick={() => setStep(2)}
                className="bg-slate-900 text-white px-8 py-4 rounded-2xl font-black text-sm hover:bg-slate-800 transition-all shadow-xl shadow-slate-200 flex items-center gap-2"
              >
                Continue to Scheduling <ChevronRight size={18} />
              </button>
            </div>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="p-10 space-y-8">
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Preferred Date</label>
                <div className="relative group">
                  <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18} />
                  <input 
                    type="date" 
                    className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-2xl text-sm font-bold focus:ring-4 focus:ring-blue-50 outline-none transition-all"
                    value={bookingData.date}
                    onChange={(e) => setBookingData({ ...bookingData, date: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-4">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Preferred Time</label>
                <div className="relative group">
                  <Clock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18} />
                  <select 
                    className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-2xl text-sm font-bold focus:ring-4 focus:ring-blue-50 outline-none transition-all appearance-none"
                    value={bookingData.time}
                    onChange={(e) => setBookingData({ ...bookingData, time: e.target.value })}
                  >
                    <option value="">Select Time Slot</option>
                    <option value="08:00 AM">08:00 AM - 09:00 AM</option>
                    <option value="09:00 AM">09:00 AM - 10:00 AM</option>
                    <option value="10:00 AM">10:00 AM - 11:00 AM</option>
                  </select>
                </div>
              </div>
            </div>

            <label className="flex items-center gap-4 p-6 rounded-2xl bg-indigo-50 border border-indigo-100 cursor-pointer transition-all hover:bg-indigo-100">
               <input 
                type="checkbox" 
                className="w-5 h-5 rounded-lg border-indigo-200 text-indigo-600 focus:ring-indigo-500"
                checked={bookingData.homeCollection}
                onChange={(e) => setBookingData({ ...bookingData, homeCollection: e.target.checked })}
               />
               <div className="flex-1">
                 <p className="text-sm font-black text-indigo-900">Enable Home Collection</p>
                 <p className="text-[10px] text-indigo-500 font-bold uppercase tracking-tighter mt-0.5">Recommended for senior citizens · Additional $5.00</p>
               </div>
               <MapPin size={24} className="text-indigo-400 opacity-30" />
            </label>

            <div className="flex items-center justify-between pt-6 border-t border-slate-50">
              <button 
                onClick={() => setStep(1)}
                className="text-slate-400 font-bold text-sm hover:text-slate-600"
              >
                Back to Tests
              </button>
              <button 
                onClick={handleBooking}
                disabled={loading || !bookingData.date || !bookingData.time}
                className="bg-blue-600 text-white px-10 py-4 rounded-2xl font-black text-sm hover:bg-blue-700 transition-all shadow-xl shadow-blue-100 flex items-center gap-3 disabled:opacity-50"
              >
                {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <CreditCard size={18} />}
                Confirm Booking
              </button>
            </div>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="p-16 text-center space-y-8">
            <div className="w-24 h-24 bg-green-50 text-green-500 rounded-[2rem] flex items-center justify-center mx-auto shadow-xl shadow-green-100 animate-bounce">
              <CheckCircle2 size={48} />
            </div>
            <div>
              <h2 className="text-3xl font-black tracking-tight text-slate-900">Appointment Confirmed!</h2>
              <p className="text-slate-400 font-bold text-sm mt-3 max-w-sm mx-auto leading-relaxed">
                Your slot for <span className="text-blue-600">{bookingData.testType}</span> has been successfully scheduled for <span className="text-slate-900">{bookingData.date} at {bookingData.time}</span>.
              </p>
            </div>
            <div className="flex flex-col gap-3 max-w-xs mx-auto pt-4">
              <Link href="/dashboard" className="w-full py-4 bg-slate-900 text-white rounded-2xl font-black text-sm hover:bg-slate-800 transition-all shadow-xl shadow-slate-200">
                Go to Dashboard
              </Link>
              <button className="w-full py-4 text-slate-400 font-bold text-sm hover:text-slate-600 transition-all">
                Download Receipt
              </button>
            </div>
          </motion.div>
        )}
      </div>

      <div className="p-8 bg-blue-50 rounded-[2.5rem] border border-blue-100 flex gap-6 items-center">
        <div className="w-12 h-12 bg-white text-blue-600 rounded-xl flex items-center justify-center shrink-0 shadow-lg shadow-blue-100">
          <FlaskConical size={24} />
        </div>
        <div>
          <h4 className="font-black text-blue-900 uppercase tracking-widest text-[10px] mb-1">What happens next?</h4>
          <p className="text-[11px] text-blue-700 font-bold leading-relaxed italic">
            A certified technician will collect your sample. Once analyzed, Results will automatically appear in your VisionDX portal with full AI interpretation.
          </p>
        </div>
      </div>
    </div>
  );
}

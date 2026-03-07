"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/authStore";
import api from "@/services/api";
import { motion } from "framer-motion";

const ROLES = [
  { value: "patient", label: "Patient", icon: "👤", desc: "View your reports & AI tips" },
  { value: "doctor", label: "Doctor", icon: "👨‍⚕️", desc: "Monitor patient risks" },
  { value: "lab", label: "Lab Center", icon: "🔬", desc: "Manage test bookings" },
  { value: "developer", label: "Developer", icon: "💻", desc: "Build with our API" },
];

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "patient",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const resp = await api.post("/auth/register", formData);
      const { access_token } = resp.data;

      // Fetch user info
      const userResp = await api.get("/auth/me", {
        headers: { Authorization: `Bearer ${access_token}` },
      });
      const user = userResp.data;

      setAuth(user, access_token);

      // Redirect based on role
      switch (user.role) {
        case "doctor":
          router.push("/doctor");
          break;
        case "lab":
          router.push("/lab");
          break;
        case "developer":
          router.push("/developer");
          break;
        default:
          router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed. Try a different email.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f8fafc] py-12 px-6">
      <motion.div 
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-xl bg-white rounded-3xl shadow-xl border border-gray-100 p-8 md:p-10"
      >
        <div className="text-center mb-10">
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Create Account</h1>
          <p className="text-gray-500 mt-2 text-sm">Join the VisionDX health network</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">Full Name</label>
              <input
                type="text"
                required
                className="w-full px-5 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-50/50 outline-none transition-all"
                placeholder="John Doe"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">Email</label>
              <input
                type="email"
                required
                className="w-full px-5 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-50/50 outline-none transition-all"
                placeholder="john@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">Password</label>
            <input
              type="password"
              required
              className="w-full px-5 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-50/50 outline-none transition-all"
              placeholder="Min. 8 characters"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 ml-1">Select Your Role</label>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {ROLES.map((r) => (
                <div
                  key={r.value}
                  onClick={() => setFormData({ ...formData, role: r.value })}
                  className={`cursor-pointer p-4 rounded-2xl border transition-all text-center ${
                    formData.role === r.value 
                      ? "border-blue-500 bg-blue-50 shadow-sm" 
                      : "border-gray-100 bg-gray-50/50 hover:bg-gray-50"
                  }`}
                >
                  <div className="text-2xl mb-2">{r.icon}</div>
                  <div className={`text-xs font-bold ${formData.role === r.value ? "text-blue-700" : "text-gray-700"}`}>{r.label}</div>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-gray-400 mt-3 italic text-center">
              {ROLES.find(r => r.value === formData.role)?.desc}
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-100 hover:shadow-blue-200 hover:-translate-y-0.5 active:translate-y-0 transition-all disabled:opacity-50"
          >
            {loading ? "Creating Account..." : "Join VisionDX"}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-gray-50 text-center">
          <p className="text-sm text-gray-500">
            Already have an account?{" "}
            <Link href="/login" className="text-blue-600 font-bold hover:underline">
              Sign in here
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}

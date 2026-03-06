"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const CATEGORIES = [
  { label: "Metabolic",    color: "#2563eb", icon: "🍬" },
  { label: "Hematologic",  color: "#8b5cf6", icon: "🩸" },
  { label: "Renal",        color: "#0d9488", icon: "💧" },
  { label: "Hepatic",      color: "#f59e0b", icon: "🧪" },
  { label: "Endocrine",    color: "#ec4899", icon: "🦋" },
  { label: "Nutritional",  color: "#10b981", icon: "💊" },
  { label: "Cardiovascular", color: "#ef4444", icon: "🫀" },
  { label: "Immunologic",  color: "#f97316", icon: "🛡️" },
];

export default function AnalyticsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/reports?limit=100`).then(r=>r.json())
      .then(d => setReports(Array.isArray(d) ? d : d.reports ?? []))
      .catch(()=>{}).finally(()=>setLoading(false));
  }, []);

  // Monthly volume (last 6 months)
  const monthlyData = MONTHS.slice(-6).map((m, i) => ({
    month: m,
    count: Math.max(0, reports.filter(r => {
      const date = r.created_at ? new Date(r.created_at) : null;
      return date && date.getMonth() === (new Date().getMonth() - 5 + i + 12) % 12;
    }).length),
  }));
  const maxMonth = Math.max(...monthlyData.map(d => d.count), 1);

  const totalReports    = reports.length;
  const totalAbnormal   = reports.reduce((s,r) => s + (r.abnormal_count||0), 0);
  const totalParameters = reports.reduce((s,r) => s + (r.total_parameters||0), 0);
  const avgAbnormal     = totalReports ? (totalAbnormal / totalReports).toFixed(1) : "0";

  return (
    <div className="page-content animate-fade-in">
      <div style={{ marginBottom: 24 }}>
        <h1 className="page-title">Analytics</h1>
        <p className="page-subtitle">Lab report statistics and disease trends</p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 14, marginBottom: 28 }} className="stagger animate-slide-up">
        {[
          { n: totalReports,    label: "Total Reports",         icon: "📋", color: "var(--blue-600)",   bg: "var(--blue-50)" },
          { n: totalParameters, label: "Parameters Analyzed",   icon: "🧪", color: "var(--purple-600)", bg: "var(--purple-50)" },
          { n: totalAbnormal,   label: "Abnormal Flags",        icon: "🚩", color: "var(--danger)",     bg: "var(--danger-bg)" },
          { n: avgAbnormal,     label: "Avg Flags / Report",    icon: "📊", color: "var(--teal-600)",   bg: "var(--teal-50)" },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-card-icon" style={{ background: s.bg }}><span style={{ fontSize: 20 }}>{s.icon}</span></div>
            <div>
              <div style={{ fontSize: 26, fontWeight: 800, color: s.color, lineHeight: 1 }}>{s.n}</div>
              <div style={{ fontSize: 11.5, color: "var(--gray-400)", marginTop: 4 }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 20, alignItems: "start" }}>
        {/* Monthly chart */}
        <div className="card animate-slide-up" style={{ padding: 20 }}>
          <p style={{ fontWeight: 700, fontSize: 14, color: "var(--gray-800)", marginBottom: 20 }}>📈 Monthly Report Volume</p>
          {loading ? (
            <div className="skeleton" style={{ height: 180 }} />
          ) : (
            <div style={{ display: "flex", alignItems: "flex-end", gap: 12, height: 180 }}>
              {monthlyData.map(d => (
                <div key={d.month} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: "var(--blue-600)" }}>{d.count || ""}</span>
                  <div style={{
                    width: "100%", borderRadius: 6,
                    height: `${Math.max(d.count / maxMonth * 150, d.count > 0 ? 8 : 0)}px`,
                    background: d.count > 0
                      ? "linear-gradient(180deg,var(--blue-500),var(--blue-700))"
                      : "var(--gray-100)",
                    transition: "height 0.6s var(--ease)",
                    minHeight: 4,
                  }} />
                  <span style={{ fontSize: 11, color: "var(--gray-400)" }}>{d.month}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Category breakdown */}
        <div className="card animate-slide-left" style={{ padding: 20 }}>
          <p style={{ fontWeight: 700, fontSize: 14, color: "var(--gray-800)", marginBottom: 16 }}>🏥 Disease Categories</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {CATEGORIES.map((cat, i) => {
              const pct = Math.round(Math.random() * 80 + 10); // Static placeholder until API provides this
              return (
                <div key={cat.label}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--gray-700)", display: "flex", alignItems: "center", gap: 5 }}>
                      {cat.icon} {cat.label}
                    </span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: cat.color }}>{pct}%</span>
                  </div>
                  <div className="progress-track">
                    <div style={{ height: "100%", borderRadius: 999, background: cat.color, width: `${pct}%`, animation: `progressFill 0.8s ${i*0.1}s var(--ease) both` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Most abnormal parameters */}
      <div className="card animate-slide-up" style={{ marginTop: 20, overflow: "hidden" }}>
        <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--gray-100)" }}>
          <span style={{ fontWeight: 700, fontSize: 14, color: "var(--gray-800)" }}>🔬 Most Commonly Flagged Tests</span>
        </div>
        <table className="data-table">
          <thead><tr>{["Test","Direction","Clinical Significance","Category"].map(h=><th key={h}>{h}</th>)}</tr></thead>
          <tbody>
            {[
              ["Vitamin D",       "LOW",  "Bone health, immune function, mood",        "Nutritional",    "badge-low"],
              ["Hemoglobin",      "LOW",  "Anemia — fatigue, weakness",                "Hematologic",    "badge-low"],
              ["Glucose",         "HIGH", "Diabetes risk — insulin resistance",        "Metabolic",      "badge-high"],
              ["Vitamin B12",     "LOW",  "Nerve damage, megaloblastic anemia",        "Nutritional",    "badge-low"],
              ["TSH",             "HIGH", "Hypothyroidism — fatigue, weight gain",     "Endocrine",      "badge-high"],
              ["Triglycerides",   "HIGH", "Cardiovascular risk, metabolic syndrome",   "Lipid",          "badge-high"],
              ["ALT",             "HIGH", "Liver inflammation / fatty liver",          "Hepatic",        "badge-high"],
              ["IgE",             "HIGH", "Allergic disease / atopic conditions",      "Immunologic",    "badge-high"],
              ["Homocysteine",    "HIGH", "Stroke, cardiovascular disease risk",       "Cardiovascular", "badge-high"],
            ].map(([test, dir, sig, cat, cls]) => (
              <tr key={String(test)}>
                <td style={{ fontWeight: 600, color: "var(--gray-800)" }}>{test}</td>
                <td><span className={String(cls)}>{dir}</span></td>
                <td style={{ fontSize: 12.5, color: "var(--gray-500)" }}>{sig}</td>
                <td><span className="badge-blue" style={{ fontSize: 11 }}>{cat}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

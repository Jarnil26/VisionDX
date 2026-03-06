"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const QUICK_ACTIONS = [
  { icon: "📤", label: "Upload Report",   href: "/upload",    color: "var(--blue-600)",   bg: "var(--blue-50)" },
  { icon: "🔬", label: "View Analysis",   href: "/report",    color: "var(--purple-600)", bg: "var(--purple-50)" },
  { icon: "📊", label: "Analytics",       href: "/analytics", color: "var(--teal-600)",   bg: "var(--teal-50)" },
  { icon: "👨‍⚕️", label: "Find Doctor",   href: "/doctor",    color: "var(--success)",   bg: "var(--success-bg)" },
];

const AI_TIPS = [
  "Vitamin D deficiency is found in 70-80% of South Asian populations due to indoor lifestyles.",
  "Homocysteine > 15 μmol/L doubles cardiovascular risk — ensure B12 and folate are adequate.",
  "HbA1c reflects 3-month average glucose — more reliable than fasting glucose alone.",
  "MPV (Mean Platelet Volume) > 10.3 fL is an early cardiovascular risk marker.",
  "CRP > 10 mg/L indicates active inflammation — check for infection or autoimmune disease.",
];

export default function DashboardPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tip] = useState(() => AI_TIPS[Math.floor(Math.random() * AI_TIPS.length)]);

  useEffect(() => {
    fetch(`${API}/reports?limit=6`).then(r => r.json()).then(d => {
      setHistory(Array.isArray(d) ? d : d.reports ?? []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const stats = [
    { n: history.length, label: "Reports Analyzed", icon: "📋", color: "var(--blue-600)",   bg: "var(--blue-50)" },
    { n: history.filter(r => r.abnormal_count > 0).length, label: "With Abnormal Values", icon: "⚠️", color: "var(--warning)", bg: "var(--warning-bg)" },
    { n: history.reduce((s, r) => s + (r.total_parameters ?? 0), 0), label: "Parameters Analyzed", icon: "🧪", color: "var(--purple-600)", bg: "var(--purple-50)" },
    { n: history.filter(r => r.total_parameters > 0).length, label: "Successful Parses", icon: "✅", color: "var(--success)", bg: "var(--success-bg)" },
  ];

  return (
    <div className="page-content animate-fade-in">
      {/* Page header */}
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Overview of lab reports and AI analysis</p>
      </div>

      {/* Stat cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: 14, marginBottom: 28 }} className="stagger animate-slide-up">
        {stats.map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-card-icon" style={{ background: s.bg }}>
              <span style={{ fontSize: 20 }}>{s.icon}</span>
            </div>
            <div>
              {loading
                ? <div className="skeleton" style={{ width: 40, height: 28, marginBottom: 6 }} />
                : <div style={{ fontSize: 28, fontWeight: 800, color: s.color, lineHeight: 1 }}>{s.n}</div>}
              <div style={{ fontSize: 12, color: "var(--gray-400)", marginTop: 4 }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 20, alignItems: "start" }}>
        {/* Recent reports */}
        <div className="card animate-slide-up" style={{ overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--gray-100)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 700, fontSize: 14, color: "var(--gray-800)" }}>📂 Recent Reports</span>
            <a href="/history" style={{ fontSize: 12, color: "var(--blue-600)", fontWeight: 600 }}>View all →</a>
          </div>
          {loading ? (
            <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 12 }}>
              {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 50 }} />)}
            </div>
          ) : history.length === 0 ? (
            <div style={{ padding: "40px 20px", textAlign: "center" }}>
              <div style={{ fontSize: 36, marginBottom: 10 }}>📂</div>
              <p style={{ color: "var(--gray-500)", fontWeight: 600, marginBottom: 6 }}>No reports yet</p>
              <a href="/upload" className="btn-primary btn-sm">Upload your first report</a>
            </div>
          ) : (
            <table className="data-table">
              <thead><tr>{["Patient","Report ID","Parameters","Abnormal","Date"].map(h=><th key={h}>{h}</th>)}</tr></thead>
              <tbody>
                {history.map((r: any, i: number) => (
                  <tr key={i} style={{ cursor: "pointer" }} onClick={() => window.location.href = `/report?id=${r.report_id}`}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                        <div style={{
                          width: 30, height: 30, borderRadius: 8, flexShrink: 0,
                          background: "linear-gradient(135deg,var(--blue-500),var(--purple-600))",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 12, fontWeight: 800, color: "white",
                        }}>{(r.patient_name || "?")?.[0]?.toUpperCase()}</div>
                        <span style={{ fontWeight: 600, fontSize: 13 }}>{r.patient_name || "Unknown"}</span>
                      </div>
                    </td>
                    <td><span className="code-tag">{r.report_id}</span></td>
                    <td><span style={{ fontWeight: 700, color: "var(--blue-600)" }}>{r.total_parameters ?? 0}</span></td>
                    <td>
                      {r.abnormal_count > 0
                        ? <span className="badge-high">{r.abnormal_count}</span>
                        : <span className="badge-normal">0</span>}
                    </td>
                    <td style={{ color: "var(--gray-400)", fontSize: 12 }}>{r.created_at?.split("T")[0] ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Quick actions */}
          <div className="card" style={{ padding: 20 }}>
            <p style={{ fontWeight: 700, fontSize: 13, color: "var(--gray-700)", marginBottom: 14 }}>⚡ Quick Actions</p>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {QUICK_ACTIONS.map(a => (
                <a key={a.label} href={a.href} style={{
                  display: "flex", alignItems: "center", gap: 11, padding: "10px 14px",
                  borderRadius: 12, background: a.bg, border: `1px solid ${a.bg}`,
                  fontSize: 13, fontWeight: 600, color: a.color, textDecoration: "none",
                  transition: "transform 150ms ease, box-shadow 150ms ease",
                }}
                  onMouseEnter={e => { (e.currentTarget as HTMLElement).style.transform = "translateX(3px)"; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.transform = "none"; }}
                >
                  <span style={{ fontSize: 18 }}>{a.icon}</span> {a.label}
                </a>
              ))}
            </div>
          </div>

          {/* AI tip */}
          <div className="ai-panel">
            <p style={{ fontWeight: 700, fontSize: 12, color: "var(--purple-700,#6d28d9)", marginBottom: 8 }}>💡 Clinical Insight</p>
            <p style={{ fontSize: 13, color: "var(--gray-700)", lineHeight: 1.7 }}>{tip}</p>
          </div>

          {/* System status */}
          <div className="card insight-panel" style={{ padding: 16 }}>
            <p style={{ fontWeight: 700, fontSize: 12, color: "var(--blue-800,#1e40af)", marginBottom: 10 }}>🔧 System Status</p>
            {[
              { label: "AI Engine", status: "Online" },
              { label: "LOINC Mapper", status: "Ready" },
              { label: "Disease KB", status: "30+ diseases" },
              { label: "Database", status: "SQLite Active" },
            ].map(({ label, status }) => (
              <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <span style={{ fontSize: 12, color: "var(--gray-600)" }}>{label}</span>
                <span style={{ fontSize: 11, fontWeight: 600, color: "var(--success)" }}>✓ {status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

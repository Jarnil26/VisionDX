"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const S = (c: string) => ({ LOW: "badge-low", HIGH: "badge-high", NORMAL: "badge-normal" }[c] ?? "badge-normal");

export default function HistoryPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [query,   setQuery]   = useState("");
  const [filter,  setFilter]  = useState<"all"|"abnormal"|"normal">("all");

  useEffect(() => {
    fetch(`${API}/reports?limit=100`).then(r => r.json())
      .then(d => setReports(Array.isArray(d) ? d : d.reports ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const visible = reports.filter(r => {
    const q = query.toLowerCase();
    const textMatch = !q || (r.patient_name || "").toLowerCase().includes(q) || (r.report_id || "").toLowerCase().includes(q);
    const filterMatch = filter === "all" || (filter === "abnormal" ? r.abnormal_count > 0 : r.abnormal_count === 0);
    return textMatch && filterMatch;
  });

  return (
    <div className="page-content animate-fade-in">
      <div style={{ marginBottom: 24 }}>
        <h1 className="page-title">Report History</h1>
        <p className="page-subtitle">All uploaded lab reports with analysis status</p>
      </div>

      {/* Summary stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 12, marginBottom: 24 }} className="stagger animate-slide-up">
        {[
          { n: reports.length,                                        label: "Total Reports",    icon: "📋", color: "var(--blue-600)",   bg: "var(--blue-50)" },
          { n: reports.filter(r => r.abnormal_count > 0).length,     label: "With Abnormals",  icon: "⚠️", color: "var(--warning)",    bg: "var(--warning-bg)" },
          { n: reports.filter(r => r.abnormal_count === 0).length,   label: "All Normal",      icon: "✅", color: "var(--success)",    bg: "var(--success-bg)" },
          { n: reports.reduce((s,r) => s + (r.abnormal_count||0), 0),label: "Flags Detected",  icon: "🚩", color: "var(--danger)",     bg: "var(--danger-bg)" },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-card-icon" style={{ background: s.bg }}><span style={{ fontSize: 18 }}>{s.icon}</span></div>
            <div>
              <div style={{ fontSize: 24, fontWeight: 800, color: s.color, lineHeight: 1 }}>{s.n}</div>
              <div style={{ fontSize: 11.5, color: "var(--gray-400)", marginTop: 3 }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ position: "relative", flex: 1, minWidth: 200 }}>
          <svg style={{ position: "absolute", left: 11, top: "50%", transform: "translateY(-50%)", color: "var(--gray-400)", pointerEvents: "none" }}
            width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input className="input" placeholder="Search by patient name or report ID…"
            value={query} onChange={e => setQuery(e.target.value)}
            style={{ paddingLeft: 34 }} />
        </div>
        <div className="tab-bar" style={{ padding: "3px", width: "auto" }}>
          {(["all","abnormal","normal"] as const).map(f => (
            <button key={f} className={`tab-btn ${filter===f?"active":""}`} onClick={() => setFilter(f)}>
              {f === "all" ? "All" : f === "abnormal" ? "⚠️ Abnormal" : "✅ Normal"}
            </button>
          ))}
        </div>
        <a href="/upload" className="btn-primary btn-sm">+ Upload New</a>
      </div>

      {/* Table */}
      <div className="card animate-slide-up" style={{ overflow: "hidden" }}>
        <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--gray-100)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 700, fontSize: 13, color: "var(--gray-700)" }}>Reports ({visible.length})</span>
        </div>
        {loading ? (
          <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 12 }}>
            {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 52 }} />)}
          </div>
        ) : visible.length === 0 ? (
          <div style={{ padding: "48px 20px", textAlign: "center" }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>{query ? "🔍" : "📂"}</div>
            <p style={{ color: "var(--gray-500)", fontWeight: 600, marginBottom: 6 }}>
              {query ? `No reports match "${query}"` : "No reports uploaded yet"}
            </p>
            {!query && <a href="/upload" className="btn-primary btn-sm">Upload Report</a>}
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>{["Patient","Gender / Age","Report ID","Parameters","Abnormal","Lab","Date",""].map(h => <th key={h}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {visible.map((r: any, i: number) => (
                  <tr key={i}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                        <div style={{
                          width: 32, height: 32, borderRadius: 9, flexShrink: 0,
                          background: "linear-gradient(135deg,var(--blue-500),var(--purple-600))",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 13, fontWeight: 800, color: "white",
                        }}>{(r.patient_name || "?")?.[0]?.toUpperCase()}</div>
                        <span style={{ fontWeight: 600, fontSize: 13 }}>{r.patient_name || "Unknown"}</span>
                      </div>
                    </td>
                    <td style={{ fontSize: 12, color: "var(--gray-500)" }}>
                      {[r.gender, r.age ? `${r.age}y` : null].filter(Boolean).join(" / ") || "—"}
                    </td>
                    <td><span className="code-tag">{r.report_id}</span></td>
                    <td><span style={{ fontWeight: 700, color: "var(--blue-600)" }}>{r.total_parameters ?? 0}</span></td>
                    <td>
                      {r.abnormal_count > 0
                        ? <span className="badge-high">{r.abnormal_count} flagged</span>
                        : <span className="badge-normal">Normal</span>}
                    </td>
                    <td style={{ fontSize: 12, color: "var(--gray-400)", maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {r.lab_name || "—"}
                    </td>
                    <td style={{ fontSize: 12, color: "var(--gray-400)" }}>{r.created_at?.split("T")[0] ?? "—"}</td>
                    <td>
                      <a href={`/report?id=${r.report_id}`} className="btn-outline btn-sm">View →</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

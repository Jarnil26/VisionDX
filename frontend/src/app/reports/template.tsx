"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const S = (c: string) => ({ LOW: "var(--blue-600)", HIGH: "var(--danger)", NORMAL: "var(--success)", CRITICAL: "#b91c1c" }[c] ?? "var(--gray-400)");
const CLS = (c: string) => ({ LOW: "badge-low", HIGH: "badge-high", NORMAL: "badge-normal", CRITICAL: "badge-high" }[c] ?? "badge-normal");
const PCT = (c: number) => Math.round(c * 100);

export default function ReportPage() {
  const [reportId, setReportId] = useState("");
  const [report, setReport]     = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [tab, setTab]           = useState<"overview"|"abnormal"|"prediction">("overview");

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("id");
    if (id) { setReportId(id); fetchReport(id); }
  }, []);

  async function fetchReport(id: string) {
    if (!id.trim()) return;
    setLoading(true); setError(""); setReport(null); setAnalysis(null);
    try {
      const [r, a] = await Promise.all([
        fetch(`${API}/report/${id}`).then(r => r.json()),
        fetch(`${API}/report/${id}/analysis`).then(r => r.json()),
      ]);
      if (r.detail) throw new Error(r.detail);
      setReport(r); setAnalysis(a);
    } catch (e: any) { setError(e.message || "Report not found."); }
    finally { setLoading(false); }
  }

  return (
    <div className="page-content animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Report Analysis</h1>
        <p className="page-subtitle">AI-powered analysis of extracted lab parameters</p>
      </div>

      {/* Search bar */}
      <div style={{ display: "flex", gap: 10, maxWidth: 560, marginBottom: 28 }}>
        <div style={{ position: "relative", flex: 1 }}>
          <svg style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--gray-400)", pointerEvents: "none" }}
            width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input className="input" value={reportId}
            onChange={e => setReportId(e.target.value)}
            onKeyDown={e => e.key === "Enter" && fetchReport(reportId)}
            placeholder="Enter Report ID…"
            style={{ paddingLeft: 36 }} />
        </div>
        <button className="btn-primary" onClick={() => fetchReport(reportId)} disabled={loading || !reportId.trim()}>
          {loading ? <span className="spinner-sm" style={{ borderTopColor: "white" }} /> : null}
          Search
        </button>
      </div>

      {error && <div className="danger-panel" style={{ maxWidth: 560, marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        {error}
      </div>}

      {loading && !report && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {[120, 80, 200].map((h, i) => <div key={i} className="skeleton" style={{ height: h }} />)}
        </div>
      )}

      {report && !loading && (
        <>
          {/* Patient banner */}
          <div className="card animate-slide-up" style={{ padding: "20px 24px", marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, flexWrap: "wrap" }}>
              {/* Left: patient avatar + details */}
              <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
                <div style={{
                  width: 52, height: 52, borderRadius: 14, flexShrink: 0,
                  background: "linear-gradient(135deg,var(--blue-500),var(--purple-600))",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 20, fontWeight: 800, color: "white",
                }}>
                  {(report.patient_name || report.patient?.name || "?")[0]?.toUpperCase()}
                </div>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 800, color: "var(--gray-900)", letterSpacing: "-0.3px" }}>
                    {report.patient_name || report.patient?.name || "Unknown Patient"}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 5, flexWrap: "wrap" }}>
                    {report.age    || report.patient?.age   ? <span className="badge-blue">{report.age || report.patient?.age} yrs</span> : null}
                    {report.gender || report.patient?.gender ? <span className="badge-blue">{report.gender || report.patient?.gender}</span> : null}
                    {report.lab_name ? <span style={{ fontSize: 12, color: "var(--gray-400)" }}>🏥 {report.lab_name}</span> : null}
                  </div>
                </div>
              </div>
              {/* Right: IDs */}
              <div style={{ display: "flex", gap: 28, flexWrap: "wrap" }}>
                {[
                  ["Report ID",  report.report_id],
                  ["Date",       report.report_date || report.date || "—"],
                ].map(([l, v]) => (
                  <div key={l}>
                    <p style={{ fontSize: 10.5, color: "var(--gray-400)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>{l}</p>
                    <p style={{ fontWeight: 700, fontSize: 13.5, color: l === "Report ID" ? "var(--blue-700)" : "var(--gray-800)", marginTop: 3, fontFamily: "monospace" }}>{v || "—"}</p>
                  </div>
                ))}
                <span className="badge-normal" style={{ alignSelf: "center" }}>✓ Processed</span>
              </div>
            </div>
          </div>

          {/* Stat cards */}
          {analysis && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 12, marginBottom: 24 }}
              className="stagger animate-slide-up">
              {[
                { n: analysis.total_parameters, label: "Total Parameters", icon: "🧪", bg: "var(--blue-50)",    color: "var(--blue-600)" },
                { n: analysis.normal_count,     label: "Normal",           icon: "✅", bg: "var(--success-bg)", color: "var(--success)" },
                { n: analysis.abnormal_count,   label: "Abnormal",         icon: "⚠️", bg: "var(--danger-bg)",  color: "var(--danger)" },
                { n: report.parameters?.filter((p:any)=>p.status==="HIGH").length ?? 0, label: "Elevated", icon: "📈", bg: "var(--warning-bg)", color: "var(--warning)" },
                { n: report.parameters?.filter((p:any)=>p.status==="LOW").length  ?? 0, label: "Low",      icon: "📉", bg: "var(--info-bg)",    color: "var(--blue-500)" },
              ].map(s => (
                <div key={s.label} className="card" style={{ padding: "16px 18px", display: "flex", alignItems: "center", gap: 14 }}>
                  <div style={{ width: 42, height: 42, borderRadius: 12, background: s.bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>
                    {s.icon}
                  </div>
                  <div>
                    <div style={{ fontSize: 22, fontWeight: 800, color: s.color, lineHeight: 1 }}>{s.n}</div>
                    <div style={{ fontSize: 11.5, color: "var(--gray-400)", marginTop: 3 }}>{s.label}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tabs */}
          <div className="tab-bar" style={{ maxWidth: 460, marginBottom: 20 }}>
            {[
              { k: "overview",   label: "📋 All Parameters" },
              { k: "abnormal",   label: "🚨 Abnormal" },
              { k: "prediction", label: "🤖 AI Prediction" },
            ].map(t => (
              <button key={t.k} className={`tab-btn ${tab===t.k?"active":""}`} onClick={() => setTab(t.k as any)}>{t.label}</button>
            ))}
          </div>

          {/* Tab content */}
          <div className="animate-fade-in">

            {/* Overview */}
            {tab === "overview" && (
              <div className="card animate-scale-in" style={{ overflow: "hidden" }}>
                <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--gray-100)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: "var(--gray-800)" }}>All Parameters</span>
                  <span className="badge-blue">{report.parameters?.length ?? 0} extracted</span>
                </div>
                <div style={{ overflowX: "auto" }}>
                  <table className="data-table">
                    <thead><tr>{["Parameter","Value","Unit","Reference Range","Status"].map(h=><th key={h}>{h}</th>)}</tr></thead>
                    <tbody>
                      {report.parameters?.map((p:any, i:number) => (
                        <tr key={i} className={p.status==="HIGH"?"row-high":p.status==="LOW"?"row-low":""}>
                          <td style={{ fontWeight: 600, color: "var(--gray-800)" }}>{p.name}</td>
                          <td style={{ fontWeight: 700, color: S(p.status), fontSize: 15 }}>{p.value??"-"}</td>
                          <td style={{ color: "var(--gray-400)", fontSize: 12 }}>{p.unit||"—"}</td>
                          <td style={{ color: "var(--gray-400)", fontSize: 12, fontFamily: "monospace" }}>{p.reference_range||"—"}</td>
                          <td><span className={CLS(p.status)}>{p.status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Abnormal */}
            {tab === "abnormal" && analysis && (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }} className="animate-scale-in">
                <div className="insight-panel">
                  <p style={{ fontSize: 13, fontWeight: 700, color: "var(--blue-800,#1e40af)", marginBottom: 6 }}>📋 Clinical Summary</p>
                  <p style={{ fontSize: 14, color: "var(--gray-700)", lineHeight: 1.8 }}>{analysis.summary}</p>
                </div>
                <div className="card" style={{ overflow: "hidden" }}>
                  <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--gray-100)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 700, color: "var(--gray-800)" }}>🚨 Abnormal Values</span>
                    {analysis.abnormal_count > 0 && <span className="badge-high">{analysis.abnormal_count} flagged</span>}
                  </div>
                  <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 8 }}>
                    {analysis.parameters?.filter((p:any)=>p.status!=="NORMAL").map((p:any, i:number) => (
                      <div key={i} style={{
                        display: "flex", alignItems: "center", justifyContent: "space-between",
                        padding: "12px 16px", borderRadius: 12,
                        background: p.status==="HIGH" ? "var(--danger-bg)" : "var(--info-bg)",
                        border: `1px solid ${p.status==="HIGH" ? "var(--danger-border)" : "var(--info-border)"}`,
                        gap: 12,
                      }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <span style={{ fontSize: 16 }}>{p.status==="HIGH" ? "📈" : "📉"}</span>
                          <span style={{ fontWeight: 600, color: "var(--gray-800)", fontSize: 14 }}>{p.name}</span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 13, flexWrap: "wrap", justifyContent: "flex-end" }}>
                          <span style={{ fontWeight: 800, color: S(p.status), fontSize: 15 }}>{p.value} <span style={{ fontSize: 11, fontWeight: 500 }}>{p.unit}</span></span>
                          <span style={{ color: "var(--gray-400)", fontSize: 12 }}>Ref: {p.reference_range||"—"}</span>
                          <span className={CLS(p.status)}>{p.status}</span>
                        </div>
                      </div>
                    ))}
                    {analysis.abnormal_count === 0 && (
                      <div style={{ textAlign: "center", padding: "32px 0" }}>
                        <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
                        <p style={{ color: "var(--success)", fontWeight: 700, fontSize: 15 }}>All Parameters Normal</p>
                        <p style={{ color: "var(--gray-400)", fontSize: 13, marginTop: 4 }}>No abnormal values detected</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Prediction */}
            {tab === "prediction" && <PredictionTab reportId={report.report_id} />}
          </div>
        </>
      )}
    </div>
  );
}

function PredictionTab({ reportId }: { reportId: string }) {
  const [data, setData]   = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const COLORS = ["#2563eb","#8b5cf6","#0d9488","#f59e0b","#ef4444","#10b981","#ec4899","#f97316"];

  useEffect(() => {
    fetch(`${API}/report/${reportId}/prediction`).then(r=>r.json()).then(setData).finally(()=>setLoading(false));
  }, [reportId]);

  if (loading) return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 76 }} />)}
    </div>
  );

  const conditions = data?.possible_conditions ?? [];
  if (!conditions.length) return (
    <div className="card animate-scale-in" style={{ padding: 48, textAlign: "center" }}>
      <div style={{ fontSize: 44, marginBottom: 14 }}>🤖</div>
      <p style={{ fontWeight: 700, color: "var(--gray-700)", fontSize: 16, marginBottom: 6 }}>AI Analysis Complete</p>
      <p style={{ fontSize: 13, color: "var(--gray-400)", marginBottom: 16 }}>No significant conditions detected based on available parameters.</p>
      <div className="code-tag">python -m visiondx.ml.train_model</div>
    </div>
  );

  return (
    <div className="animate-scale-in">
      <div className="ai-panel" style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 14, fontWeight: 700, color: "var(--purple-700,#6d28d9)", marginBottom: 4 }}>🤖 AI Disease Prediction Engine</p>
        <p style={{ fontSize: 12.5, color: "var(--gray-500)", lineHeight: 1.6 }}>
          Evidence-based analysis using LOINC-mapped biomarkers and clinical rules.
          Always consult a qualified physician before clinical decisions.
        </p>
      </div>
      <div style={{ display: "grid", gap: 10 }}>
        {conditions.map((p: any, i: number) => {
          const pct = PCT(p.confidence);
          const c   = COLORS[i % COLORS.length];
          const isCrit = pct >= 80;
          return (
            <div key={i} className="prediction-card" style={{ borderLeft: `3px solid ${c}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <div>
                  <div style={{ fontWeight: 700, color: "var(--gray-900)", fontSize: 14.5 }}>{p.disease}</div>
                  {p.reason && <div style={{ fontSize: 11.5, color: "var(--gray-400)", marginTop: 2 }}>↳ {p.reason}</div>}
                </div>
                <div style={{ textAlign: "center", flexShrink: 0, marginLeft: 12 }}>
                  <div style={{ fontSize: 22, fontWeight: 900, color: c, lineHeight: 1 }}>{pct}%</div>
                  <div style={{ fontSize: 10, color: "var(--gray-400)", marginTop: 2 }}>confidence</div>
                </div>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${pct}%`, background: c }} />
              </div>
            </div>
          );
        })}
      </div>
      <div className="warning-panel" style={{ marginTop: 16 }}>
        <p style={{ fontSize: 12, color: "#92400e", lineHeight: 1.6 }}>
          ⚠️ <strong>Medical Disclaimer:</strong> This AI analysis is for informational purposes only.
          Always consult a licensed physician or medical professional for diagnosis and treatment.
        </p>
      </div>
    </div>
  );
}

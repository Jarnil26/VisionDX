"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TABS = ["signup", "docs", "examples"] as const;
type Tab = typeof TABS[number];

const PLANS = [
  { name: "Free",       price: "₹0/mo",    limit: "100 req/day",  color: "var(--gray-700)",   bg: "var(--gray-50)",    features: ["PDF upload & text analysis","Disease prediction","LOINC mapping","JSON response"] },
  { name: "Pro",        price: "₹999/mo",  limit: "5,000 req/day",color: "var(--blue-700)",   bg: "var(--blue-50)",    features: ["Everything in Free","Batch processing","Priority support","Advanced analytics","Webhook callbacks"] },
  { name: "Enterprise", price: "Custom",   limit: "Unlimited",    color: "var(--purple-700)", bg: "var(--purple-50)",  features: ["Everything in Pro","SLA guarantee","On-prem deployment","Custom LOINC mapping","Dedicated support"] },
];

const CODE_EXAMPLES = {
  curl: `# 1. Upload a lab report PDF
curl -X POST https://api.visiondx.app/api/v1/analyze \\
  -H "X-API-Key: vdx_your_key_here" \\
  -F "file=@/path/to/report.pdf"

# Response:
# { "report_id": "VDX-20260306-ABC123", "status": "done" }

# 2. Get disease predictions
curl https://api.visiondx.app/api/v1/report/VDX-20260306-ABC123/prediction \\
  -H "X-API-Key: vdx_your_key_here"`,

  python: `import requests

API_KEY = "vdx_your_key_here"
BASE    = "https://api.visiondx.app/api/v1"
HEADERS = {"X-API-Key": API_KEY}

# Upload PDF
with open("report.pdf", "rb") as f:
    r = requests.post(f"{BASE}/analyze", headers=HEADERS, files={"file": f})
report_id = r.json()["report_id"]

# Get AI predictions
pred = requests.get(f"{BASE}/report/{report_id}/prediction", headers=HEADERS)
for cond in pred.json()["possible_conditions"]:
    print(f"{cond['disease']}: {cond['confidence']*100:.0f}%")

# Analyze raw text (no PDF needed)
text_resp = requests.post(f"{BASE}/analyze/text", headers=HEADERS, json={
    "text": "Glucose: 141 mg/dL (74-106)\\nVitamin B12: 148 pg/mL (187-833)",
    "patient_name": "John Doe", "patient_age": 45
})
print(text_resp.json())`,

  javascript: `const API_KEY = "vdx_your_key_here";
const BASE    = "https://api.visiondx.app/api/v1";

// Upload PDF
const form = new FormData();
form.append("file", pdfFile); // File object from <input type="file">

const res    = await fetch(\`\${BASE}/analyze\`, {
  method: "POST",
  headers: { "X-API-Key": API_KEY },
  body: form,
});
const { report_id } = await res.json();

// Get predictions
const pred = await fetch(\`\${BASE}/report/\${report_id}/prediction\`, {
  headers: { "X-API-Key": API_KEY }
});
const { possible_conditions } = await pred.json();
console.log(possible_conditions);
// [{ disease: "Diabetes Mellitus", confidence: 0.92 }, ...]

// Analyze text directly
const textRes = await fetch(\`\${BASE}/analyze/text\`, {
  method: "POST",
  headers: { "X-API-Key": API_KEY, "Content-Type": "application/json" },
  body: JSON.stringify({ text: "Glucose: 141 mg/dL\\nHbA1c: 7.2%", patient_age: 45 })
});`,
};

const RESPONSE_EXAMPLES = {
  prediction: `{
  "report_id": "VDX-20260306-ABC123",
  "possible_conditions": [
    { "disease": "Diabetes Mellitus (Type 2)", "confidence": 0.9317 },
    { "disease": "Vitamin B12 Deficiency",     "confidence": 0.8714 },
    { "disease": "Allergic Disease / Atopy",    "confidence": 0.8241 },
    { "disease": "Cardiovascular Risk",          "confidence": 0.7805 }
  ]
}`,
  analysis: `{
  "report_id": "VDX-20260306-ABC123",
  "total_parameters": 76,
  "abnormal_count": 8,
  "normal_count": 68,
  "summary": "8 abnormal values detected. Elevated: Glucose, IgE, Homocysteine, MPV. Below normal: Vitamin B12, Urea, HbA, BUN.",
  "parameters": [
    { "name": "Glucose",     "value": 141.0, "unit": "mg/dL", "reference_range": "74-106", "status": "HIGH" },
    { "name": "Vitamin B12", "value": 148.0, "unit": "pg/mL", "reference_range": "187-833","status": "LOW"  },
    { "name": "IgE",         "value": 492.3, "unit": "IU/mL", "reference_range": "0-87",   "status": "HIGH" }
  ]
}`,
};

export default function DeveloperPage() {
  const [tab, setTab]         = useState<Tab>("docs");
  const [codeTab, setCodeTab] = useState<"curl"|"python"|"javascript">("python");
  const [respTab, setRespTab] = useState<"prediction"|"analysis">("prediction");
  const [form, setForm]       = useState({ full_name: "", email: "", password: "", org_name: "", use_case: "" });
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<any>(null);
  const [error, setError]     = useState("");
  const [copied, setCopied]   = useState("");

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/developer/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Signup failed");
      setResult(json);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  function copyToClipboard(text: string, id: string) {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(""), 2000);
  }

  const CopyBtn = ({ text, id }: { text: string; id: string }) => (
    <button onClick={() => copyToClipboard(text, id)} style={{
      position: "absolute", top: 10, right: 10,
      background: copied === id ? "var(--success)" : "rgba(255,255,255,0.15)",
      border: "none", color: "white", borderRadius: 8,
      padding: "4px 10px", fontSize: 11, fontWeight: 600, cursor: "pointer",
      transition: "background 200ms ease",
    }}>
      {copied === id ? "✓ Copied" : "Copy"}
    </button>
  );

  return (
    <div className="page-content animate-fade-in">
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Developer Portal</h1>
        <p className="page-subtitle">Integrate VisionDX AI medical analysis into your application</p>
      </div>

      {/* Hero banner */}
      <div className="card-blue animate-slide-up" style={{ padding: "28px 32px", marginBottom: 28 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 20 }}>
          <div>
            <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>🚀 VisionDX Public API v1</h2>
            <p style={{ opacity: 0.85, fontSize: 14, lineHeight: 1.7, maxWidth: 500 }}>
              Upload any lab report PDF — we extract parameters, detect abnormal values,
              and predict diseases using AI. Integrate in minutes.
            </p>
            <p style={{ marginTop: 10, fontSize: 13, opacity: 0.7 }}>
              Base URL: <strong>https://api.visiondx.app/api/v1</strong>
            </p>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 40, fontWeight: 900, opacity: 0.9 }}>100</div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>Free requests/day</div>
            <button className="btn-outline" style={{ marginTop: 12, borderColor: "rgba(255,255,255,0.4)", color: "white" }}
              onClick={() => setTab("signup")}>
              Get API Key →
            </button>
          </div>
        </div>
      </div>

      {/* Main tabs */}
      <div className="tab-bar" style={{ maxWidth: 360, marginBottom: 28 }}>
        {[
          { k: "docs",    label: "📖 API Docs" },
          { k: "signup",  label: "🔑 Get API Key" },
          { k: "examples",label: "💻 Code Examples" },
        ].map(t => (
          <button key={t.k} className={`tab-btn ${tab===t.k?"active":""}`} onClick={() => setTab(t.k as Tab)}>{t.label}</button>
        ))}
      </div>

      {/* ── DOCS TAB ── */}
      {tab === "docs" && (
        <div className="animate-scale-in" style={{ display: "grid", gap: 20 }}>

          {/* Endpoint reference */}
          <div className="card" style={{ overflow: "hidden" }}>
            <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--gray-100)" }}>
              <span style={{ fontWeight: 700, fontSize: 14 }}>📡 API Endpoints</span>
            </div>
            <table className="data-table">
              <thead><tr><th>Method</th><th>Endpoint</th><th>Description</th><th>Auth</th></tr></thead>
              <tbody>
                {[
                  ["GET",  "/ping",                              "Health check — is API online?",          "None"],
                  ["POST", "/analyze",                          "Upload PDF → get report_id",             "API Key"],
                  ["POST", "/analyze/text",                     "Send raw OCR text → instant analysis",   "API Key"],
                  ["GET",  "/report/{id}",                      "Get full parsed report JSON",            "API Key"],
                  ["GET",  "/report/{id}/analysis",             "Get abnormal values + summary",          "API Key"],
                  ["GET",  "/report/{id}/prediction",           "Get AI disease predictions",             "API Key"],
                  ["POST", "/developer/signup",                 "Register → receive API key",             "None"],
                  ["GET",  "/developer/me",                     "Get account + key info",                 "Dev Credentials"],
                  ["GET",  "/developer/usage",                  "Today's usage stats",                    "Dev Credentials"],
                ].map(([m, ep, desc, auth]) => (
                  <tr key={String(ep)}>
                    <td><span className={`badge ${m==="GET"?"badge-blue":"badge-purple"}`}>{m}</span></td>
                    <td><code style={{ fontFamily: "monospace", fontSize: 12, color: "var(--blue-700)" }}>{ep}</code></td>
                    <td style={{ fontSize: 13 }}>{desc}</td>
                    <td><span className={auth === "None" ? "badge-normal" : "badge-warning"} style={{ fontSize: 10 }}>{auth}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Authentication */}
          <div className="card" style={{ padding: 24 }}>
            <h3 style={{ fontWeight: 700, fontSize: 14, marginBottom: 14 }}>🔐 Authentication</h3>
            <p style={{ fontSize: 13.5, color: "var(--gray-600)", lineHeight: 1.7, marginBottom: 16 }}>
              Include your API key in the <strong>X-API-Key</strong> header on every request.
            </p>
            <div style={{ position: "relative", background: "var(--gray-900)", borderRadius: 12, padding: "14px 16px" }}>
              <CopyBtn text='X-API-Key: vdx_your_key_here' id="auth-header" />
              <code style={{ color: "#86efac", fontSize: 13, fontFamily: "monospace" }}>X-API-Key: vdx_your_key_here</code>
            </div>
            <div className="warning-panel" style={{ marginTop: 14 }}>
              <p style={{ fontSize: 12.5, color: "#92400e" }}>
                ⚠️ Never expose your API key in client-side code or public repositories.
                Use environment variables or a secret manager.
              </p>
            </div>
          </div>

          {/* Response format */}
          <div className="card" style={{ padding: 24 }}>
            <h3 style={{ fontWeight: 700, fontSize: 14, marginBottom: 14 }}>📋 Response Format</h3>
            <div className="tab-bar" style={{ maxWidth: 300, marginBottom: 14 }}>
              {(["prediction","analysis"] as const).map(t => (
                <button key={t} className={`tab-btn ${respTab===t?"active":""}`} onClick={() => setRespTab(t)}>
                  {t === "prediction" ? "Prediction" : "Analysis"}
                </button>
              ))}
            </div>
            <div style={{ position: "relative", background: "var(--gray-900)", borderRadius: 12, padding: "16px 20px", overflowX: "auto" }}>
              <CopyBtn text={RESPONSE_EXAMPLES[respTab]} id={`resp-${respTab}`} />
              <pre style={{ color: "#a5f3fc", fontSize: 12.5, fontFamily: "monospace", whiteSpace: "pre-wrap", margin: 0 }}>
                {RESPONSE_EXAMPLES[respTab]}
              </pre>
            </div>
          </div>

          {/* Error codes */}
          <div className="card" style={{ overflow: "hidden" }}>
            <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--gray-100)" }}>
              <span style={{ fontWeight: 700, fontSize: 14 }}>⚠️ Error Codes</span>
            </div>
            <table className="data-table">
              <thead><tr><th>Status</th><th>Code</th><th>Meaning</th></tr></thead>
              <tbody>
                {[
                  ["400", "Bad Request",          "Invalid file type or malformed request"],
                  ["401", "Unauthorized",          "Missing or invalid API key"],
                  ["404", "Not Found",             "Report ID does not exist"],
                  ["413", "Payload Too Large",     "PDF exceeds 20 MB limit"],
                  ["429", "Too Many Requests",     "Daily rate limit exceeded — upgrade plan"],
                  ["500", "Internal Server Error", "Pipeline error — contact support"],
                ].map(([code, name, desc]) => (
                  <tr key={code}>
                    <td><span className={["400","401","413","429","500"].includes(String(code)) ? "badge-high" : "badge-normal"}>{code}</span></td>
                    <td style={{ fontWeight: 600, fontSize: 13 }}>{name}</td>
                    <td style={{ fontSize: 12.5, color: "var(--gray-500)" }}>{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Plans */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 16 }}>
            {PLANS.map(plan => (
              <div key={plan.name} className="card" style={{ padding: 22 }}>
                <div style={{ fontSize: 22, fontWeight: 900, color: plan.color }}>{plan.name}</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: "var(--gray-900)", margin: "6px 0" }}>{plan.price}</div>
                <div style={{ fontSize: 12, color: "var(--gray-400)", marginBottom: 16 }}>{plan.limit}</div>
                {plan.features.map(f => (
                  <div key={f} style={{ display: "flex", gap: 7, fontSize: 12.5, color: "var(--gray-600)", marginBottom: 6 }}>
                    <span style={{ color: "var(--success)" }}>✓</span> {f}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── SIGNUP TAB ── */}
      {tab === "signup" && (
        <div className="animate-scale-in" style={{ maxWidth: 520 }}>
          {result ? (
            <div className="success-panel">
              <div style={{ fontSize: 32, marginBottom: 12 }}>🎉</div>
              <h3 style={{ fontWeight: 800, fontSize: 17, color: "#065f46", marginBottom: 8 }}>API Key Generated!</h3>
              <p style={{ fontSize: 12.5, color: "#065f46", marginBottom: 16 }}>
                ⚠️ <strong>Save this key now</strong> — it won't be shown again.
              </p>
              <div style={{ position: "relative", background: "var(--gray-900)", borderRadius: 12, padding: "14px 16px", marginBottom: 14 }}>
                <CopyBtn text={result.api_key} id="new-key" />
                <code style={{ color: "#86efac", fontSize: 12.5, fontFamily: "monospace", wordBreak: "break-all", display: "block" }}>
                  {result.api_key}
                </code>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {[["Plan", result.plan], ["Daily Limit", `${result.daily_limit} requests`], ["Email", result.email], ["Prefix", result.key_prefix + "…"]].map(([l, v]) => (
                  <div key={l}>
                    <p style={{ fontSize: 10, color: "#065f46", fontWeight: 700, textTransform: "uppercase" }}>{l}</p>
                    <p style={{ fontWeight: 600, fontSize: 13, color: "#065f46" }}>{v}</p>
                  </div>
                ))}
              </div>
              <button className="btn-primary" style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
                onClick={() => setTab("docs")}>
                View Integration Docs →
              </button>
            </div>
          ) : (
            <div className="card" style={{ padding: 28 }}>
              <h3 style={{ fontWeight: 800, fontSize: 18, marginBottom: 6 }}>Get Your Free API Key</h3>
              <p style={{ fontSize: 13, color: "var(--gray-400)", marginBottom: 22 }}>
                100 requests/day free · No credit card required
              </p>
              {error && <div className="danger-panel" style={{ marginBottom: 14 }}>⚠️ {error}</div>}
              <form onSubmit={handleSignup} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: "var(--gray-600)", display: "block", marginBottom: 5 }}>Full Name *</label>
                  <input className="input" placeholder="John Doe" required value={form.full_name}
                    onChange={e => setForm(f => ({...f, full_name: e.target.value}))} />
                </div>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: "var(--gray-600)", display: "block", marginBottom: 5 }}>Email *</label>
                  <input className="input" type="email" placeholder="john@company.com" required value={form.email}
                    onChange={e => setForm(f => ({...f, email: e.target.value}))} />
                </div>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: "var(--gray-600)", display: "block", marginBottom: 5 }}>Password *</label>
                  <input className="input" type="password" placeholder="Min 8 characters" required value={form.password}
                    onChange={e => setForm(f => ({...f, password: e.target.value}))} />
                </div>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: "var(--gray-600)", display: "block", marginBottom: 5 }}>Organization (optional)</label>
                  <input className="input" placeholder="Your company or lab name" value={form.org_name}
                    onChange={e => setForm(f => ({...f, org_name: e.target.value}))} />
                </div>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: "var(--gray-600)", display: "block", marginBottom: 5 }}>How will you use the API? (optional)</label>
                  <textarea className="input" placeholder="e.g. Building a patient portal for a diagnostic lab…" rows={2}
                    value={form.use_case} onChange={e => setForm(f => ({...f, use_case: e.target.value}))}
                    style={{ resize: "vertical" }} />
                </div>
                <button className="btn-primary" type="submit" disabled={loading} style={{ marginTop: 8, justifyContent: "center" }}>
                  {loading ? <><span className="spinner-sm" style={{ borderTopColor: "white" }} /> Generating…</> : "🔑 Generate API Key"}
                </button>
                <p style={{ fontSize: 11, color: "var(--gray-300)", textAlign: "center" }}>
                  By signing up you agree to use this API responsibly for medical software only.
                </p>
              </form>
            </div>
          )}
        </div>
      )}

      {/* ── EXAMPLES TAB ── */}
      {tab === "examples" && (
        <div className="animate-scale-in" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div className="tab-bar" style={{ maxWidth: 340 }}>
            {(["python","javascript","curl"] as const).map(t => (
              <button key={t} className={`tab-btn ${codeTab===t?"active":""}`} onClick={() => setCodeTab(t)}>
                {t === "python" ? "🐍 Python" : t === "javascript" ? "🟡 JS" : "⚡ cURL"}
              </button>
            ))}
          </div>
          <div style={{ position: "relative", background: "var(--gray-900)", borderRadius: 16, padding: "20px 24px", overflowX: "auto" }}>
            <CopyBtn text={CODE_EXAMPLES[codeTab]} id={`code-${codeTab}`} />
            <pre style={{ color: "#e2e8f0", fontSize: 13, fontFamily: "monospace", whiteSpace: "pre-wrap", margin: 0, lineHeight: 1.7 }}>
              {CODE_EXAMPLES[codeTab]}
            </pre>
          </div>

          <div className="insight-panel">
            <p style={{ fontWeight: 700, fontSize: 13, color: "var(--blue-800,#1e40af)", marginBottom: 10 }}>📦 SDK Quickstart (Python)</p>
            <div style={{ background: "var(--gray-900)", borderRadius: 10, padding: "10px 14px" }}>
              <code style={{ color: "#86efac", fontSize: 12.5, fontFamily: "monospace" }}>pip install requests</code>
            </div>
            <p style={{ fontSize: 12.5, color: "var(--gray-500)", marginTop: 12, lineHeight: 1.6 }}>
              No official SDK yet — the REST API is simple enough to use directly with <strong>requests</strong> (Python),
              <strong> fetch</strong> (JS), or <strong> axios</strong>. Full SDK coming soon.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

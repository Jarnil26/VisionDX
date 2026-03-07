"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function UploadPage() {
  const [file, setFile]       = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult]   = useState<any>(null);
  const [error, setError]     = useState("");
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router   = useRouter();

  async function handleUpload() {
    if (!file) return;
    setUploading(true); setError(""); setResult(null); setProgress(0);
    const fd = new FormData();
    fd.append("file", file);
    try {
      // Simulate progress
      const interval = setInterval(() => setProgress(p => Math.min(p + 12, 88)), 400);
      const res = await fetch(`${API}/upload-report`, { method: "POST", body: fd });
      clearInterval(interval); setProgress(100);
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Upload failed");
      setResult(json);
    } catch (e: any) { setError(e.message || "Upload failed."); }
    finally { setUploading(false); }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f?.type === "application/pdf") { setFile(f); setResult(null); setError(""); }
  }

  return (
    <div className="page-content animate-fade-in">
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Upload Lab Report</h1>
        <p className="page-subtitle">Upload a PDF lab report for AI analysis</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24, alignItems: "start" }}>
        {/* Left — upload area */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Drop zone */}
          <div
            className={`drop-zone ${dragging ? "active" : ""} ${file ? "has-file" : ""}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <input ref={inputRef} type="file" accept=".pdf" style={{ display: "none" }}
              onChange={e => { const f = e.target.files?.[0]; if (f) { setFile(f); setResult(null); setError(""); } }} />
            {file ? (
              <div className="animate-scale-in">
                <div style={{ fontSize: 48, marginBottom: 12 }}>📄</div>
                <p style={{ fontWeight: 700, color: "var(--gray-800)", fontSize: 16 }}>{file.name}</p>
                <p style={{ color: "var(--gray-400)", fontSize: 13, marginTop: 4 }}>{(file.size / 1024).toFixed(1)} KB · PDF</p>
                <button className="btn-outline btn-sm" style={{ marginTop: 14 }}
                  onClick={e => { e.stopPropagation(); setFile(null); setResult(null); }}>
                  Change File
                </button>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: 48, marginBottom: 14 }} className="animate-bounce-sm">📁</div>
                <p style={{ fontWeight: 700, color: "var(--gray-700)", fontSize: 16, marginBottom: 6 }}>Drop your lab report here</p>
                <p style={{ color: "var(--gray-400)", fontSize: 13 }}>or click to browse</p>
                <p style={{ color: "var(--gray-300)", fontSize: 12, marginTop: 10 }}>PDF files only · Max 20 MB</p>
              </div>
            )}
          </div>

          {/* Progress bar during upload */}
          {uploading && (
            <div className="card animate-fade-in" style={{ padding: "16px 20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--gray-700)" }}>Processing report…</span>
                <span style={{ fontSize: 13, color: "var(--blue-600)", fontWeight: 700 }}>{progress}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${progress}%`, background: "var(--blue-500)", transition: "width 0.4s ease" }} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 14 }}>
                {[
                  [progress >= 15, "📤 Uploading PDF"],
                  [progress >= 40, "🔍 Running OCR extraction"],
                  [progress >= 65, "🧪 Parsing parameters"],
                  [progress >= 88, "🤖 Running AI analysis"],
                ].map(([done, label], i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, color: done ? "var(--success)" : "var(--gray-300)" }}>
                    {done ? "✓" : "○"} {label}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {error && <div className="danger-panel animate-fade-in">⚠️ {error}</div>}

          {/* Success result */}
          {result && !uploading && (
            <div className="success-panel animate-scale-in">
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                <div style={{ fontSize: 28 }}>🎉</div>
                <div>
                  <p style={{ fontWeight: 800, fontSize: 16, color: "#065f46" }}>Analysis Complete!</p>
                  <p style={{ fontSize: 12.5, color: "#065f46", opacity: 0.8 }}>
                    {result.total_parameters} parameters extracted · {result.abnormal_count} abnormal
                  </p>
                </div>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <a href={`/report?id=${result.report_id}`} className="btn-primary" style={{ flex: 1, justifyContent: "center" }}>
                  View Full Analysis →
                </a>
                <button className="btn-outline" onClick={() => { setFile(null); setResult(null); }}>
                  Upload Another
                </button>
              </div>
            </div>
          )}

          {/* Upload button */}
          {file && !result && !uploading && (
            <button className="btn-primary btn-lg animate-fade-in" onClick={handleUpload} style={{ width: "100%", justifyContent: "center" }}>
              🚀 Analyze Report
            </button>
          )}
        </div>

        {/* Right — info panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="card ai-panel" style={{ padding: 20 }}>
            <p style={{ fontWeight: 700, fontSize: 14, color: "var(--purple-700,#6d28d9)", marginBottom: 14 }}>🤖 What VisionDX Analyzes</p>
            {[
              ["🩸", "Blood CBC (Hemoglobin, WBC, Platelets)"],
              ["🍬", "Glucose & HbA1c (Diabetes markers)"],
              ["🫀", "Lipid Panel (Cholesterol, LDL, HDL)"],
              ["🧪", "Liver Function (ALT, AST, Bilirubin)"],
              ["💧", "Kidney Function (Creatinine, BUN)"],
              ["🦋", "Thyroid (TSH, Free T3/T4)"],
              ["💊", "Vitamins (D, B12, Folate)"],
              ["🔥", "Inflammation (CRP, ESR, Homocysteine)"],
            ].map(([icon, text]) => (
              <div key={String(text)} style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8, fontSize: 13, color: "var(--gray-700)" }}>
                <span style={{ flexShrink: 0, fontSize: 15 }}>{icon}</span> {text}
              </div>
            ))}
          </div>

          <div className="insight-panel" style={{ padding: 18 }}>
            <p style={{ fontWeight: 700, fontSize: 13, color: "var(--blue-800,#1e40af)", marginBottom: 10 }}>📋 Supported Formats</p>
            {["Most Indian diagnostic labs", "NABL accredited lab PDFs", "Printed scanned reports (via OCR)", "Digital PDF exports"].map(t => (
              <div key={t} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, fontSize: 12.5, color: "var(--gray-600)" }}>
                <span className="status-dot-green" /> {t}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

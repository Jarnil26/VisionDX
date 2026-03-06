"use client";
import { useState } from "react";

const SPECIALTIES = ["All", "General Physician", "Endocrinologist", "Cardiologist", "Nephrologist", "Hematologist", "Gastroenterologist", "Neurologist"];

const DOCTORS = [
  { name: "Dr. Priya Sharma",    specialty: "Endocrinologist",      location: "Mumbai",    exp: 14, rating: 4.9, avail: true,  fee: "₹800", about: "Diabetes, thyroid disorders, hormonal imbalances" },
  { name: "Dr. Rahul Mehta",     specialty: "Cardiologist",         location: "Delhi",     exp: 20, rating: 4.8, avail: true,  fee: "₹1200", about: "Cardiovascular risk, hypertension, lipid disorders" },
  { name: "Dr. Anita Nair",      specialty: "Hematologist",         location: "Chennai",   exp: 11, rating: 4.7, avail: false, fee: "₹900", about: "Anemia, blood disorders, platelet conditions" },
  { name: "Dr. Vikram Patel",    specialty: "Gastroenterologist",   location: "Ahmedabad", exp: 16, rating: 4.8, avail: true,  fee: "₹700", about: "Liver disease, fatty liver, digestive disorders" },
  { name: "Dr. Sunita Reddy",    specialty: "Nephrologist",         location: "Hyderabad", exp: 12, rating: 4.6, avail: true,  fee: "₹850", about: "Kidney disease, creatinine management, dialysis" },
  { name: "Dr. Karthik Iyer",    specialty: "General Physician",    location: "Bengaluru", exp: 8,  rating: 4.7, avail: true,  fee: "₹500", about: "General consultations, preventive health, vitamin deficiencies" },
  { name: "Dr. Meena Goswami",   specialty: "Neurologist",          location: "Kolkata",   exp: 18, rating: 4.9, avail: false, fee: "₹1100", about: "Homocysteine-related neuropathy, B12 deficiency" },
  { name: "Dr. Arun Krishnamurthy", specialty: "Endocrinologist",   location: "Pune",      exp: 9,  rating: 4.6, avail: true,  fee: "₹750", about: "Thyroid, HbA1c monitoring, metabolic syndrome" },
  { name: "Dr. Pooja Deshpande", specialty: "General Physician",    location: "Nagpur",    exp: 6,  rating: 4.5, avail: true,  fee: "₹400", about: "Blood test interpretation, nutrition counseling" },
];

const AVATAR_COLORS = ["#2563eb","#8b5cf6","#0d9488","#f59e0b","#ef4444","#10b981","#ec4899","#f97316","#6366f1"];

function Stars({ rating }: { rating: number }) {
  return (
    <span style={{ display: "inline-flex", gap: 1 }}>
      {[1,2,3,4,5].map(i => (
        <svg key={i} width="12" height="12" viewBox="0 0 24 24"
          fill={i <= Math.floor(rating) ? "#f59e0b" : "none"}
          stroke="#f59e0b" strokeWidth="2">
          <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
        </svg>
      ))}
      <span style={{ fontSize: 11, color: "var(--gray-500)", marginLeft: 3, fontWeight: 600 }}>{rating}</span>
    </span>
  );
}

export default function DoctorPage() {
  const [query,    setQuery]    = useState("");
  const [specialty, setSpecialty] = useState("All");

  const visible = DOCTORS.filter(d => {
    const q = query.toLowerCase();
    const textMatch = !q || d.name.toLowerCase().includes(q) || d.location.toLowerCase().includes(q) || d.about.toLowerCase().includes(q);
    const specMatch = specialty === "All" || d.specialty === specialty;
    return textMatch && specMatch;
  });

  return (
    <div className="page-content animate-fade-in">
      <div style={{ marginBottom: 24 }}>
        <h1 className="page-title">Doctor Lookup</h1>
        <p className="page-subtitle">Find specialists based on your lab report findings</p>
      </div>

      {/* Search + filter */}
      <div style={{ display: "flex", gap: 10, marginBottom: 24, flexWrap: "wrap" }}>
        <div style={{ position: "relative", flex: 1, minWidth: 200 }}>
          <svg style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--gray-400)", pointerEvents: "none" }}
            width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input className="input" placeholder="Search by name, location or condition…"
            value={query} onChange={e => setQuery(e.target.value)}
            style={{ paddingLeft: 36 }} />
        </div>
        <select className="input" style={{ width: "auto", minWidth: 180, cursor: "pointer" }}
          value={specialty} onChange={e => setSpecialty(e.target.value)}>
          {SPECIALTIES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Results count */}
      <div style={{ marginBottom: 16, fontSize: 13, color: "var(--gray-400)", fontWeight: 500 }}>
        Showing {visible.length} doctor{visible.length !== 1 ? "s" : ""}
        {specialty !== "All" ? ` · ${specialty}` : ""}
        {query ? ` · "${query}"` : ""}
      </div>

      {/* Doctor cards */}
      {visible.length === 0 ? (
        <div className="card" style={{ padding: "48px 20px", textAlign: "center" }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>🔍</div>
          <p style={{ color: "var(--gray-500)", fontWeight: 600 }}>No doctors found for your search</p>
          <button className="btn-outline btn-sm" style={{ marginTop: 12 }} onClick={() => { setQuery(""); setSpecialty("All"); }}>
            Clear filters
          </button>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(320px,1fr))", gap: 16 }} className="stagger animate-slide-up">
          {visible.map((d, i) => (
            <div key={d.name} className="card-hover" style={{ padding: "20px 22px" }}>
              {/* Header */}
              <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 14 }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14, flexShrink: 0,
                  background: AVATAR_COLORS[i % AVATAR_COLORS.length],
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 18, fontWeight: 800, color: "white",
                }}>
                  {d.name.split(" ").map(w=>w[0]).join("").slice(1,3)}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 14.5, color: "var(--gray-900)" }}>{d.name}</div>
                  <div style={{ fontSize: 12.5, color: "var(--blue-600)", fontWeight: 600, marginTop: 2 }}>{d.specialty}</div>
                  <div style={{ marginTop: 4 }}><Stars rating={d.rating} /></div>
                </div>
                <span style={{
                  fontSize: 10.5, fontWeight: 700, padding: "3px 9px", borderRadius: 100,
                  background: d.avail ? "var(--success-bg)" : "var(--gray-100)",
                  color: d.avail ? "var(--success)" : "var(--gray-400)",
                  border: `1px solid ${d.avail ? "var(--success-border)" : "var(--gray-200)"}`,
                  whiteSpace: "nowrap",
                }}>
                  {d.avail ? "● Available" : "○ Busy"}
                </span>
              </div>

              {/* Details */}
              <p style={{ fontSize: 12.5, color: "var(--gray-500)", lineHeight: 1.6, marginBottom: 14 }}>{d.about}</p>
              <div className="divider" style={{ marginBottom: 14 }} />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
                <div style={{ display: "flex", gap: 14 }}>
                  <div>
                    <p style={{ fontSize: 10, color: "var(--gray-400)", fontWeight: 700, textTransform: "uppercase" }}>Location</p>
                    <p style={{ fontSize: 12.5, fontWeight: 600, color: "var(--gray-700)", marginTop: 2 }}>📍 {d.location}</p>
                  </div>
                  <div>
                    <p style={{ fontSize: 10, color: "var(--gray-400)", fontWeight: 700, textTransform: "uppercase" }}>Experience</p>
                    <p style={{ fontSize: 12.5, fontWeight: 600, color: "var(--gray-700)", marginTop: 2 }}>{d.exp} yrs</p>
                  </div>
                  <div>
                    <p style={{ fontSize: 10, color: "var(--gray-400)", fontWeight: 700, textTransform: "uppercase" }}>Consult Fee</p>
                    <p style={{ fontSize: 12.5, fontWeight: 700, color: "var(--success)", marginTop: 2 }}>{d.fee}</p>
                  </div>
                </div>
                <button
                  className={d.avail ? "btn-primary btn-sm" : "btn-outline btn-sm"}
                  disabled={!d.avail}
                  style={{ opacity: d.avail ? 1 : 0.5 }}
                >
                  {d.avail ? "Book Now" : "Unavailable"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

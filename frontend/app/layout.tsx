"use client";
import { usePathname } from "next/navigation";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>VisionDX — AI Medical Report Analysis</title>
        <meta name="description" content="AI-powered blood test analysis platform." />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body>
        <Sidebar />
        <Header />
        <main style={{ paddingLeft: "var(--sidebar-w)", paddingTop: "var(--header-h)", minHeight: "100vh" }}>
          {children}
        </main>
      </body>
    </html>
  );
}

const NAV = [
  { group: "Core", links: [
    { href: "/",          icon: "grid",      label: "Dashboard" },
    { href: "/upload",    icon: "upload",    label: "Upload Report" },
    { href: "/report",    icon: "signal",    label: "Report Analysis" },
    { href: "/history",   icon: "clock",     label: "Report History" },
  ]},
  { group: "Insights", links: [
    { href: "/analytics", icon: "bar-chart", label: "Analytics" },
    { href: "/doctor",    icon: "user",      label: "Doctor Lookup" },
  ]},
  { group: "Developer", links: [
    { href: "/developer", icon: "code",      label: "API Portal" },
  ]},
];

function Sidebar() {
  const pathname = usePathname();
  const isActive = (href: string) => href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <aside className="sidebar-glass animate-slide-in" style={{
      position: "fixed", left: 0, top: 0, height: "100vh",
      width: "var(--sidebar-w)", zIndex: 40,
      display: "flex", flexDirection: "column", padding: "0 10px",
    }}>
      {/* Logo */}
      <div style={{ padding: "18px 10px 16px", borderBottom: "1px solid var(--gray-100)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div className="animate-float" style={{
            width: 40, height: 40, borderRadius: 12, flexShrink: 0,
            background: "linear-gradient(135deg, #2563eb, #7c3aed)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 6px 18px rgba(37,99,235,0.40)",
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <div>
            <div style={{
              fontFamily: "'Plus Jakarta Sans',sans-serif", fontWeight: 800, fontSize: 17,
              background: "linear-gradient(135deg,var(--blue-700),var(--purple-600))",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", letterSpacing: "-0.5px",
            }}>VisionDX</div>
            <div style={{ fontSize: 10.5, color: "var(--gray-400)", fontWeight: 500, marginTop: 1 }}>Medical AI Engine</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: "auto", padding: "16px 0 8px" }}>
        {NAV.map((group, gi) => (
          <div key={group.group} style={{ marginBottom: gi < NAV.length - 1 ? 22 : 0 }}>
            <div style={{
              fontSize: 9.5, fontWeight: 700, color: "var(--gray-400)", letterSpacing: "0.1em",
              textTransform: "uppercase", padding: "0 10px 8px",
            }}>{group.group}</div>
            <div className="stagger animate-slide-in" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {group.links.map(l => (
                <a key={l.href} href={l.href} className={`nav-item ${isActive(l.href) ? "active" : ""}`}>
                  <span style={{
                    width: 32, height: 32, borderRadius: 9, flexShrink: 0,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: isActive(l.href) ? "rgba(37,99,235,0.10)" : "transparent",
                    transition: "background 150ms ease",
                  }}>
                    <NavIcon name={l.icon} />
                  </span>
                  {l.label}
                </a>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Status footer */}
      <div style={{ padding: "10px 4px 16px" }}>
        <div style={{
          borderRadius: 14, padding: "12px 14px",
          background: "linear-gradient(135deg,var(--blue-50),#eef4ff)",
          border: "1px solid var(--blue-100)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 5 }}>
            <span className="status-dot-green" />
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--blue-700)" }}>System Online</span>
          </div>
          <p style={{ fontSize: 11, color: "var(--blue-500)", lineHeight: 1.5 }}>Dynamic Engine · 30+ Disease KB</p>
          <p style={{ fontSize: 11, color: "var(--blue-400)" }}>LOINC Mapped · SQLite · ML Ready</p>
        </div>
        <div style={{ marginTop: 10, textAlign: "center", fontSize: 10.5, color: "var(--gray-300)" }}>
          VisionDX v2.0 · AI Medical Platform
        </div>
      </div>
    </aside>
  );
}

function Header() {
  const pathname = usePathname();
  const allLinks = NAV.flatMap(g => g.links);
  const current  = allLinks.find(l => l.href === "/" ? pathname === "/" : pathname.startsWith(l.href));

  return (
    <header className="header-elevated animate-slide-down" style={{
      position: "fixed", left: "var(--sidebar-w)", right: 0, top: 0,
      height: "var(--header-h)", zIndex: 30,
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "0 28px",
    }}>
      <div>
        <h1 style={{ fontSize: 17, fontWeight: 700, color: "var(--gray-900)", letterSpacing: "-0.3px" }}>
          {current?.label ?? "VisionDX"}
        </h1>
        <p style={{ fontSize: 11.5, color: "var(--gray-400)", marginTop: 1 }}>
          {new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
        </p>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {/* Search */}
        <div style={{ position: "relative" }}>
          <svg style={{ position: "absolute", left: 11, top: "50%", transform: "translateY(-50%)", color: "var(--gray-400)", pointerEvents: "none" }}
            width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input placeholder="Search reports…" style={{
            paddingLeft: 32, paddingRight: 14, height: 36,
            borderRadius: 10, border: "1px solid var(--gray-200)",
            fontSize: 13, color: "var(--gray-700)", outline: "none",
            background: "var(--gray-50)", width: 210,
          }} />
        </div>

        {/* Bell */}
        <button style={{
          width: 36, height: 36, borderRadius: 10, border: "1px solid var(--gray-200)",
          background: "white", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
          color: "var(--gray-500)", position: "relative",
        }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <span style={{
            position: "absolute", top: 7, right: 7, width: 6, height: 6,
            borderRadius: "50%", background: "var(--blue-500)", border: "1.5px solid white",
          }} />
        </button>

        {/* Avatar */}
        <div style={{
          width: 36, height: 36, borderRadius: 10, cursor: "pointer",
          background: "linear-gradient(135deg,var(--blue-500),var(--purple-600))",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 2px 8px rgba(37,99,235,0.30)", flexShrink: 0,
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
          </svg>
        </div>
      </div>
    </header>
  );
}

function NavIcon({ name }: { name: string }) {
  const P: Record<string, React.ReactNode> = {
    "grid":      <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
    "upload":    <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17,8 12,3 7,8"/><line x1="12" y1="3" x2="12" y2="15"/></>,
    "signal":    <><polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/></>,
    "clock":     <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>,
    "bar-chart": <><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></>,
    "user":      <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></>,
  };
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {P[name]}
    </svg>
  );
}

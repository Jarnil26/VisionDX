"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import "./globals.css";
import Providers from "./providers";
import { useAuthStore } from "@/store/authStore";
import Link from "next/link";
import { 
  LayoutDashboard, 
  FileText, 
  Activity, 
  UserCircle, 
  Code, 
  FlaskConical, 
  Bell, 
  Search, 
  LogOut,
  MessageSquare,
  CalendarDays,
  Menu,
  ChevronRight
} from "lucide-react";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuthStore();
  const isAuthPage = pathname === "/login" || pathname === "/register";

  useEffect(() => {
    if (!isAuthenticated && !isAuthPage && pathname !== "/") {
      router.push("/login");
    }
  }, [isAuthenticated, isAuthPage, pathname, router]);

  return (
    <html lang="en">
      <head>
        <title>VisionDX — AI Medical Report Analysis</title>
        <meta name="description" content="AI-powered blood test analysis platform." />
      </head>
      <body className="bg-slate-50 text-slate-900 antialiased font-sans">
        <Providers>
          {isAuthPage ? (
            children
          ) : (
            <div className="flex">
              {isAuthenticated && <Sidebar userRole={user?.role} pathname={pathname} logout={logout} />}
              <div className={`flex-1 min-h-screen ${isAuthenticated ? "pl-64" : ""}`}>
                {isAuthenticated && <Header userName={user?.full_name} pathname={pathname} />}
                <main className={isAuthenticated ? "pt-16" : ""}>
                  {children}
                </main>
              </div>
            </div>
          )}
        </Providers>
      </body>
    </html>
  );
}

const NAV_CONFIG = {
  patient: [
    { group: "Health Control", links: [
      { href: "/dashboard", icon: LayoutDashboard, label: "Overview" },
      { href: "/reports",   icon: FileText,        label: "My Reports" },
      { href: "/chat",      icon: MessageSquare,   label: "AI Doctor Chat" },
    ]},
    { group: "Services", links: [
      { href: "/labs",      icon: FlaskConical,    label: "Book Lab Test" },
      { href: "/followups", icon: Activity,        label: "Health Followups" },
    ]},
  ],
  doctor: [
    { group: "Clinical", links: [
      { href: "/doctor",    icon: LayoutDashboard, label: "Doctor Dashboard" },
      { href: "/doctor/patients", icon: UserCircle,  label: "Patient Archive" },
    ]},
  ],
  lab: [
    { group: "Operations", links: [
      { href: "/lab",       icon: CalendarDays,    label: "Lab Bookings" },
      { href: "/lab/upload", icon: FlaskConical,    label: "Process Report" },
    ]},
  ],
  developer: [
    { group: "Engineering", links: [
      { href: "/developer", icon: Code,           label: "Dev Portal" },
      { href: "/developer/docs", icon: FileText,    label: "API Reference" },
    ]},
  ],
};

function Sidebar({ userRole, pathname, logout }: { userRole: any, pathname: string, logout: () => void }) {
  const navItems = NAV_CONFIG[userRole as keyof typeof NAV_CONFIG] || NAV_CONFIG.patient;

  const isActive = (href: string) => {
    if (href === "/dashboard" && pathname === "/") return true;
    return pathname.startsWith(href);
  };

  return (
    <aside className="w-64 h-screen fixed left-0 top-0 bg-white border-r border-slate-200 flex flex-col z-50 transition-all duration-300">
      <div className="p-6 flex items-center gap-3 border-b border-slate-50">
        <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-100">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
        </div>
        <div>
          <h1 className="text-lg font-black tracking-tight bg-gradient-to-r from-blue-700 to-indigo-600 bg-clip-text text-transparent">VisionDX</h1>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">AI Medical Intelligence</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto p-4 space-y-8 mt-4">
        {navItems.map((group, idx) => (
          <div key={idx} className="space-y-2">
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] px-3">{group.group}</h3>
            <div className="space-y-1">
              {group.links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all group ${
                    isActive(link.href) 
                      ? "bg-blue-50 text-blue-700 shadow-sm" 
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <link.icon size={18} className={isActive(link.href) ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600"} />
                  {link.label}
                  {isActive(link.href) && <ChevronRight size={14} className="ml-auto opacity-50" />}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-100">
        <button 
          onClick={() => { logout(); window.location.href = "/login"; }}
          className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-bold text-slate-500 hover:bg-red-50 hover:text-red-600 transition-all"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}

function Header({ userName, pathname }: { userName: any, pathname: string }) {
  const getPageTitle = () => {
    const segments = pathname.split("/").filter(Boolean);
    if (segments.length === 0) return "Dashboard Overview";
    return segments[0].charAt(0).toUpperCase() + segments[0].slice(1);
  };

  return (
    <header className="h-16 fixed top-0 right-0 left-64 bg-white/80 backdrop-blur-md border-b border-slate-200 z-40 flex items-center justify-between px-8">
      <div className="flex items-center gap-4">
        <h2 className="text-sm font-bold text-slate-800">{getPageTitle()}</h2>
        <div className="h-4 w-[1px] bg-slate-200"></div>
        <p className="text-xs text-slate-400 font-medium">
          {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </p>
      </div>

      <div className="flex items-center gap-6">
        <div className="relative group hidden md:block">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
          <input 
            type="text" 
            placeholder="Search your health data..." 
            className="bg-slate-50 border-none rounded-full pl-10 pr-4 py-2 text-xs w-64 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          />
        </div>

        <button className="relative p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-full transition-all">
          <Bell size={18} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full border-2 border-white"></span>
        </button>

        <div className="flex items-center gap-3 pl-4 border-l border-slate-100">
          <div className="text-right">
            <p className="text-xs font-bold text-slate-800 leading-tight">{userName || "Guest User"}</p>
            <p className="text-[10px] text-blue-600 font-black uppercase tracking-tighter mt-0.5">Verified Account</p>
          </div>
          <div className="w-9 h-9 bg-gradient-to-br from-slate-100 to-slate-200 rounded-full border border-slate-200 flex items-center justify-center text-slate-400 font-black text-sm shadow-inner">
            {userName?.[0] || "G"}
          </div>
        </div>
      </div>
    </header>
  );
}

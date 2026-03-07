"use client";

import { useState, useRef, useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import api from "@/services/api";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, 
  Stethoscope, 
  User, 
  Zap, 
  ShieldCheck, 
  HelpCircle,
  Plus,
  RefreshCw,
  MoreVertical
} from "lucide-react";
import { SafeMarkdown } from "@/components/chat/SafeMarkdown";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function ChatPage() {
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: `Hello ${user?.full_name?.split(" ")[0] || "there"}! I am your VisionDX AI Doctor. I can help interpret your blood reports or answer general health questions. How can I assist you today?`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const resp = await api.post("/chat", { message: input });
      
      let replyText = resp.data.reply || "I'm sorry, I couldn't process that. Please try again.";
      
      // Append emergency alert info if present
      if (resp.data.emergency_alert && resp.data.nearby_facilities?.length) {
        replyText += "\n\n#### 🚨 Nearby Emergency Facilities\n";
        resp.data.nearby_facilities.forEach((f: any) => {
          replyText += `• **${f.name}** — ${f.address} (${f.phone})\n`;
        });
      }
      
      // Append suggestions if present
      if (resp.data.suggestions?.length) {
        resp.data.suggestions.forEach((s: any) => {
          if (s.type === "possible_conditions" && s.items?.length) {
            replyText += "\n\n#### 📊 " + s.title + "\n";
            s.items.forEach((item: any) => {
              replyText += `• **${item.condition}** (${(item.confidence * 100).toFixed(0)}%)\n`;
            });
          }
        });
      }
      
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: replyText,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: err?.message?.includes("Auth failed") 
          ? "Your session has expired. Please log in again to continue chatting."
          : "I'm currently unable to connect. Please check your connection and try again.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-64px)] flex flex-col pt-4 overflow-hidden">
      <div className="flex-1 max-w-4xl w-full mx-auto flex flex-col bg-white md:rounded-t-[3rem] shadow-2xl shadow-slate-200 border-x border-t border-slate-100 relative">
        {/* Chat Header */}
        <div className="p-6 border-b border-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-blue-100">
              <Stethoscope size={24} />
            </div>
            <div>
              <h2 className="text-lg font-black text-slate-900 tracking-tight">VisionDX AI Consultant</h2>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Medical Intelligence Active</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-3 text-slate-400 hover:bg-slate-50 rounded-xl transition-all"><RefreshCw size={18} /></button>
            <button className="p-3 text-slate-400 hover:bg-slate-50 rounded-xl transition-all"><MoreVertical size={18} /></button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 scrollbar-hide">
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-sm transition-transform hover:scale-105 ${
                  msg.role === "assistant" 
                    ? "bg-blue-600 text-white shadow-blue-100" 
                    : "bg-slate-900 text-white shadow-slate-100"
                }`}>
                  {msg.role === "assistant" ? <Zap size={18} /> : <span>{user?.full_name?.[0] || "U"}</span>}
                </div>
                
                <div className={`max-w-[85%] space-y-2 ${msg.role === "user" ? "text-right" : ""}`}>
                  <div className={`p-6 rounded-[2rem] shadow-sm border border-slate-50 transition-all ${
                    msg.role === "assistant" 
                      ? "bg-white text-slate-700 rounded-tl-none ring-1 ring-slate-100/50" 
                      : "bg-blue-600 text-white rounded-tr-none shadow-xl shadow-blue-100/50"
                  }`}>
                    {msg.role === "assistant" ? (
                      <SafeMarkdown content={msg.content} />
                    ) : (
                      <p className="text-sm font-medium leading-relaxed">{msg.content}</p>
                    )}
                  </div>
                  <p className="px-2 text-[10px] font-black text-slate-300 uppercase tracking-widest flex items-center gap-2 justify-end">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    {msg.role === "assistant" && <ShieldCheck size={10} className="text-blue-400" />}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {isLoading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
              <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center animate-pulse">
                <Zap size={18} />
              </div>
              <div className="bg-slate-50 p-5 rounded-3xl rounded-tl-none flex gap-2 items-center">
                <span className="w-1.5 h-1.5 bg-indigo-300 rounded-full animate-bounce"></span>
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce delay-100"></span>
                <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce delay-200"></span>
              </div>
            </motion.div>
          )}
          <div ref={scrollRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 md:p-8 bg-white md:rounded-b-[3rem]">
          <form onSubmit={handleSend} className="relative group">
            <input 
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your hemoglobin levels, vitals, or generic health tips..."
              className="w-full pl-6 pr-16 py-5 bg-slate-50 border-none rounded-2xl text-sm font-medium focus:ring-4 focus:ring-blue-50 outline-none transition-all placeholder:text-slate-400 shadow-inner"
            />
            <button 
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-3 top-1/2 -translate-y-1/2 w-12 h-12 bg-blue-600 text-white rounded-xl flex items-center justify-center shadow-lg shadow-blue-100 hover:bg-blue-700 hover:-translate-y-0.5 transition-all disabled:opacity-30 disabled:translate-y-0"
            >
              <Send size={20} />
            </button>
          </form>
          
          <div className="flex flex-wrap justify-center gap-4 mt-6">
            <div className="flex items-center gap-1 text-[10px] font-black text-slate-300 uppercase tracking-widest border border-slate-50 px-3 py-1.5 rounded-full">
              <ShieldCheck size={12} /> HIPAA Compliant
            </div>
            <div className="flex items-center gap-1 text-[10px] font-black text-slate-300 uppercase tracking-widest border border-slate-50 px-3 py-1.5 rounded-full">
              <Zap size={12} /> Real-time Knowledge
            </div>
            <div className="flex items-center gap-1 text-[10px] font-black text-slate-300 uppercase tracking-widest border border-slate-50 px-3 py-1.5 rounded-full">
              <HelpCircle size={12} /> 24/7 Availability
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

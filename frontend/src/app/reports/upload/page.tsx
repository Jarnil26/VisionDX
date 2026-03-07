"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import api from "@/services/api";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle2, 
  Loader2, 
  AlertCircle,
  FileUp,
  BrainCircuit,
  Microscope,
  Stethoscope
} from "lucide-react";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<"idle" | "uploading" | "processing" | "success" | "error">("idle");
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const router = useRouter();

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setStatus("idle");
      setError("");
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: false,
  });

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setStatus("uploading");
    setProgress(20);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Step 1: Upload
      const resp = await api.post("/upload-report", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          setProgress(20 + (percent * 0.3)); // Max 50% for upload
        }
      });

      const { report_id } = resp.data;
      
      // Step 2: Start Processing Animation
      setStatus("processing");
      setProgress(70);
      
      // Artificial delay to show processing phases
      setTimeout(() => setProgress(85), 1000);
      setTimeout(() => setProgress(95), 2000);

      // Verify processing status (backend is sync for now in this project)
      setStatus("success");
      setProgress(100);

      setTimeout(() => {
        router.push(`/reports/${report_id}`);
      }, 1500);

    } catch (err: any) {
      setStatus("error");
      setError(err.response?.data?.detail || "Upload failed. Please ensure the PDF is valid.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-black tracking-tight text-slate-900">Upload Lab Report</h1>
        <p className="text-slate-400 font-bold text-sm uppercase tracking-widest">Powered by VisionDX OCR Engine</p>
      </div>

      <div className="grid md:grid-cols-3 gap-8 items-start">
        <div className="md:col-span-2 space-y-6">
          <div 
            {...getRootProps()} 
            className={`relative group cursor-pointer aspect-video rounded-[2.5rem] border-4 border-dashed transition-all flex flex-col items-center justify-center p-12 text-center overflow-hidden ${
              isDragActive ? "border-blue-500 bg-blue-50/50" : 
              file ? "border-green-500 bg-green-50/20" : 
              "border-slate-100 bg-white hover:border-blue-200 hover:bg-slate-50/50"
            }`}
          >
            <input {...getInputProps()} />
            
            <AnimatePresence mode="wait">
              {status === "idle" ? (
                <motion.div 
                  key="idle"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="space-y-4"
                >
                  <div className="w-20 h-20 bg-blue-50 text-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-6 transition-transform group-hover:scale-110 group-hover:rotate-3 shadow-lg shadow-blue-100">
                    <Upload size={32} />
                  </div>
                  {file ? (
                    <div className="space-y-1">
                      <p className="font-black text-slate-900">{file.name}</p>
                      <p className="text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB · Ready to Analyze</p>
                    </div>
                  ) : (
                    <div>
                      <h3 className="text-lg font-black text-slate-900">Drag your PDF here</h3>
                      <p className="text-sm text-slate-400 font-medium">or click to browse from computer</p>
                    </div>
                  )}
                </motion.div>
              ) : (
                <motion.div 
                  key="active"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="w-full space-y-8 px-12"
                >
                  <div className="flex justify-between items-end mb-2">
                    <div className="space-y-1">
                      <p className="text-sm font-black text-slate-900 uppercase tracking-widest">
                        {status === "uploading" ? "Uploading to Cloud..." : 
                         status === "processing" ? "AI Engine Parsing..." : 
                         status === "success" ? "Analysis Complete" : "Error Detected"}
                      </p>
                      <p className="text-xs text-slate-400 font-bold">
                        {status === "processing" ? "Extracting biomarkers & medical markers" : "Connecting to VisionDX Core"}
                      </p>
                    </div>
                    <span className="text-2xl font-black text-blue-600">{progress}%</span>
                  </div>
                  
                  <div className="h-4 bg-slate-100 rounded-full overflow-hidden p-1 shadow-inner">
                    <motion.div 
                      className={`h-full rounded-full ${status === "error" ? "bg-red-500" : "bg-gradient-to-r from-blue-500 to-indigo-600"}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>

                  {status === "success" && (
                    <div className="flex items-center justify-center gap-2 text-green-600 font-black animate-bounce">
                      <CheckCircle2 size={24} /> Redirecting to results...
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {file && status === "idle" && (
              <button 
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                className="absolute top-6 right-6 p-2 bg-white text-slate-400 hover:text-red-500 rounded-xl shadow-md border border-slate-100 transition-all"
              >
                <X size={18} />
              </button>
            )}
          </div>

          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-red-50 border border-red-100 rounded-2xl flex items-center gap-3 text-red-600"
              >
                <AlertCircle size={20} />
                <p className="text-sm font-bold">{error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          <button
            onClick={handleUpload}
            disabled={!file || uploading || status === "success"}
            className="w-full py-5 bg-slate-900 text-white rounded-[2rem] font-black text-lg shadow-2xl shadow-slate-200 hover:bg-slate-800 hover:-translate-y-1 disabled:opacity-30 disabled:translate-y-0 transition-all flex items-center justify-center gap-3"
          >
            {uploading ? <Loader2 className="animate-spin" /> : <FileUp />} Start AI Analysis
          </button>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-sm space-y-6">
            <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest border-b border-slate-50 pb-4">Our Analysis Flow</h3>
            
            <div className="space-y-6">
              {[
                { icon: Microscope, title: "OCR Extraction", desc: "Digital text extraction from PDFs", color: "text-blue-500", bg: "bg-blue-50" },
                { icon: BrainCircuit, title: "Medical Parsing", desc: "Parameter normalization (LOINC)", color: "text-purple-500", bg: "bg-purple-50" },
                { icon: Stethoscope, title: "Disease Prediction", desc: "AI-driven health risk assessment", color: "text-indigo-500", bg: "bg-indigo-50" }
              ].map((step, i) => (
                <div key={i} className="flex gap-4">
                  <div className={`w-10 h-10 ${step.bg} ${step.color} rounded-xl flex items-center justify-center shrink-0`}>
                    <step.icon size={18} />
                  </div>
                  <div>
                    <h4 className="text-xs font-black text-slate-800">{step.title}</h4>
                    <p className="text-[10px] text-slate-400 font-bold leading-relaxed">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-8 bg-blue-50 rounded-[2rem] border border-blue-100">
            <h4 className="text-xs font-black text-blue-700 uppercase tracking-widest mb-2">Supported Formats</h4>
            <p className="text-[10px] text-blue-500 font-bold leading-relaxed italic">
              Currently supporting all standard blood test, urine test, and thyroid profiles in PDF format. Keep file size under 20MB.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

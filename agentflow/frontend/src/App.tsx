// src/App.tsx
import { useCallback, useRef, useState, useEffect } from "react";
import { Loader2, Bot, User2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import cn from "classnames";

import { useTasks } from "./hooks/useTasks";
import { Button } from "./components/ui/button";
import { Card, CardContent } from "./components/ui/card";
import type { Task } from "./types";

export default function App() {
  const { tasks, connected } = useTasks();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [timer, setTimer] = useState(0);

  // Timer effect
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (loadingTasks) {
      setTimer(0);
      interval = setInterval(() => setTimer((t) => t + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [loadingTasks]);

  // Stop loading when tasks arrive
  useEffect(() => {
    if (loadingTasks && tasks.length > 0) {
      setLoadingTasks(false);
    }
  }, [loadingTasks, tasks.length]);

  const byStatus = useCallback(
    (s: Task["status"]) => tasks.filter((t) => t.status === s),
    [tasks]
  );

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) return;
    setUploading(true);
    setLoadingTasks(true);
    const fd = new FormData();
    fd.append("file", selectedFile);
    try {
      const res = await fetch(
        import.meta.env.VITE_API_URL ?? "http://localhost:8000/projects",
        { method: "POST", body: fd }
      );
      if (!res.ok) throw new Error(await res.text());
      setSelectedFile(null);
    } catch (err: any) {
      alert("Upload failed: " + err.message);
    } finally {
      setUploading(false);
    }
  }

  const Column = ({ status, label }: { status: Task["status"]; label: string }) => (
    <div className="flex-shrink-0 w-80 flex flex-col glass rounded-2xl p-4 shadow-lg">
      <h2 className="mb-4 flex items-center justify-between text-lg font-semibold">
        {label}
        {status === "in_progress" && <Loader2 className="animate-spin text-blue-500" size={18} />}
      </h2>
      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        {loadingTasks && tasks.length === 0 ? (
          // skeleton placeholders
          [0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-24 bg-gray-200 rounded-lg animate-pulse"
            />
          ))
        ) : (
          <AnimatePresence>
            {byStatus(status).map((task) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                layout
              >
                <Card
                  className={cn(
                    "glass border border-white/30 shadow-md overflow-hidden",
                    task.routedTo === "ai" ? "border-blue-400" : "border-emerald-400"
                  )}
                >
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-start gap-3">
                      {task.routedTo === "ai" ? (
                        <Bot size={20} className="text-blue-600" />
                      ) : (
                        <User2 size={20} className="text-emerald-600" />
                      )}
                      <div className="flex-1">
                        <p className="font-medium line-clamp-2 leading-tight">
                          {task.title}
                        </p>
                        <p className="mt-1 text-xs text-gray-600">
                          {task.routedTo === "ai" ? "AI Agent" : "Human"}: {task.owner ?? "—"}
                        </p>
                      </div>
                    </div>
                    {task.result && (
                      <div className="whitespace-pre-wrap rounded bg-white/80 p-2 text-sm text-gray-800">
                        {task.result}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );

  // format timer as MM:SS
  const minutes = String(Math.floor(timer / 60)).padStart(2, '0');
  const seconds = String(timer % 60).padStart(2, '0');

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-indigo-50 via-white to-pink-50 p-6">
      {/* Header */}
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">AgentFlow Demo</h1>
        <div className="flex items-center gap-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.pdf"
            className="hidden"
            onChange={handleFileChange}
          />
          <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
            Choose File
          </Button>
          <span className="text-sm text-gray-700 max-w-[10rem] truncate">
            {selectedFile?.name ?? "No file chosen"}
          </span>
          <Button
            variant="primary"
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
          >
            {uploading ? "Uploading…" : "Upload Spec"}
          </Button>
          <span
            className={cn(
              "h-4 w-4 rounded-full",
              connected ? "bg-emerald-500" : "bg-red-400"
            )}
            title={connected ? "Connected" : "Disconnected"}
          />
        </div>
      </header>

      {/* Loading status & timer */}
      {loadingTasks && tasks.length === 0 && (
        <div className="mb-4 text-center text-gray-600">
          <Loader2 className="inline animate-spin mr-2 text-gray-500" size={16} />
          Currently processing the project… {minutes}:{seconds}
        </div>
      )}

      {/* Board */}
      <div className="flex flex-row flex-1 gap-6 overflow-x-auto pb-4">
        <Column status="queued" label="Queued" />
        <Column status="in_progress" label="In Progress" />
        <Column status="done" label="Done" />
      </div>

      {/* Footer */}
      <footer className="mt-6 text-center text-sm text-gray-500">
        Developed by Adrian Dsouza: Demo – AI ↔ Human orchestration
      </footer>
    </div>
  );
}

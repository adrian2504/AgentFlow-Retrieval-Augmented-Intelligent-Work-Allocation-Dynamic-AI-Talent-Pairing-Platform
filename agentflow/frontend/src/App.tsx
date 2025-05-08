/* frontend/src/App.tsx */
import { useEffect, useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Bot, User2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import cn from "classnames";

type Task = {
  id: string;
  title: string;
  status: "queued" | "in_progress" | "done";
  routed_to: "ai" | "human";        // matches backend JSON
  owner?: string | null;
};

export default function App() {
  /* ───────── State ───────── */
  const [tasks, setTasks] = useState<Task[]>([]);
  const [connected, setConnected] = useState(false);
  const [uploading, setUploading] = useState(false);

  /* ───────── WebSocket live updates ───────── */
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/tasks");
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      const data: Task = JSON.parse(e.data);
      setTasks((prev) => {
        const other = prev.filter((t) => t.id !== data.id);
        return [...other, data];
      });
    };
    return () => ws.close();
  }, []);

  /* ─ Helpers ─ */
  const byStatus = useCallback(
    (s: Task["status"]) => tasks.filter((t) => t.status === s),
    [tasks],
  );

  /* ─ File upload handler ─ */
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    setUploading(true);
    try {
      const res = await fetch("http://localhost:8000/projects", {
        method: "POST",
        body: fd,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(`Server error: ${err.detail ?? res.statusText}`);
        setUploading(false);
        return;
      }
    } catch (err) {
      alert("Network error: " + (err as Error).message);
    } finally {
      setUploading(false);
      e.target.value = ""; // reset file input
    }
  };

  /* ─ Re‑usable Column component ─ */
  const Column = ({
    status,
    label,
  }: {
    status: Task["status"];
    label: string;
  }) => (
    <div className="flex-1 p-2 min-w-[280px]">
      <h2 className="text-xl font-semibold mb-2 flex items-center gap-2">
        {label}
        {status === "in_progress" && <Loader2 className="animate-spin" size={18} />}
      </h2>
      <div className="space-y-2">
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
                  "border-2",
                  task.routed_to === "ai"
                    ? "border-blue-400"
                    : "border-emerald-400",
                )}
              >
                <CardContent className="p-3 flex items-center gap-3">
                  {task.routed_to === "ai" ? <Bot size={20} /> : <User2 size={20} />}
                  <div className="flex-1">
                    <p className="font-medium leading-tight line-clamp-2">
                      {task.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {task.routed_to === "ai" ? "AI Agent: " : "Human: "}
                      {task.owner ?? "—"}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );

  /* ───────── UI ───────── */
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4 flex flex-col">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">AgentFlow Demo</h1>
        <div className="flex items-center gap-3">
          <input
            id="file"
            type="file"
            className="hidden"
            onChange={handleUpload}
            accept=".pdf,.md,.txt"
          />
          <label htmlFor="file">
            <Button variant="secondary" disabled={uploading}>
              {uploading ? (
                <span className="flex items-center gap-1">
                  <Loader2 className="animate-spin" size={16} /> Uploading…
                </span>
              ) : (
                "Upload Project Spec"
              )}
            </Button>
          </label>
          {/* WebSocket indicator */}
          <div
            className={cn(
              "h-3 w-3 rounded-full",
              connected ? "bg-emerald-500" : "bg-red-400",
            )}
            title={connected ? "WS Connected" : "WS Disconnected"}
          />
        </div>
      </header>

      <div className="grid xl:grid-cols-3 md:grid-cols-2 gap-4 flex-1 overflow-x-auto">
        <Column status="queued" label="Queued" />
        <Column status="in_progress" label="In Progress" />
        <Column status="done" label="Done" />
      </div>

      <footer className="text-center text-xs text-muted-foreground mt-4">
        Demo – AI ↔ Human orchestration
      </footer>
    </div>
  );
}

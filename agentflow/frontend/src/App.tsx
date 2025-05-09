import { useCallback, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Bot, User2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import cn from "classnames";

import { useTasks } from "./hooks/useTasks";
import type { Task } from "./types";

export default function App() {
  const { tasks, connected } = useTasks();
  const [uploading, setUploading] = useState(false);

  const byStatus = useCallback(
    (s: Task["status"]) => tasks.filter((t) => t.status === s),
    [tasks]
  );

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    if (!e.target.files?.[0]) return;
    setUploading(true);

    const fd = new FormData();
    fd.append("file", e.target.files[0]);

    try {
      const res = await fetch(
        import.meta.env.VITE_API_URL ?? "http://localhost:8000/projects",
        { method: "POST", body: fd }
      );
      if (!res.ok) throw new Error(await res.text());
    } catch (err: any) {
      alert("Upload failed: " + err.message);
    } finally {
      setUploading(false);
    }
  }

  const Column = ({
    status,
    label,
  }: {
    status: Task["status"];
    label: string;
  }) => (
    <div className="flex-1 min-w-[280px] p-2">
      <h2 className="mb-2 flex items-center gap-2 text-xl font-semibold">
        {label}
        {status === "in_progress" && (
          <Loader2 className="animate-spin" size={18} />
        )}
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
                  task.routedTo === "ai"
                    ? "border-blue-400"
                    : "border-emerald-400"
                )}
              >
                <CardContent className="flex flex-col gap-3 p-3">
                  <div className="flex items-start gap-3">
                    {task.routedTo === "ai" ? (
                      <Bot size={20} />
                    ) : (
                      <User2 size={20} />
                    )}
                    <div className="flex-1">
                      <p className="line-clamp-2 font-medium leading-tight">
                        {task.title}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {task.routedTo === "ai" ? "AI Agent" : "Human"}:{" "}
                        {task.owner ?? "—"}
                      </p>
                    </div>
                  </div>

                  {task.result && (
                    <div className="whitespace-pre-wrap rounded bg-slate-50 p-2 text-sm">
                      {task.result}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      {/* ── header ─────────────────────────────────────────────── */}
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">AgentFlow Demo</h1>

        <div className="flex items-center gap-3">
          <input
            id="file"
            type="file"
            className="hidden"
            accept=".txt,.md,.pdf"
            onChange={handleUpload}
          />
          <label htmlFor="file">
            <Button variant="secondary" disabled={uploading}>
              {uploading ? "Uploading…" : "Upload Project Spec"}
            </Button>
          </label>

          {/* connection indicator */}
          <span
            className={cn(
              "h-3 w-3 rounded-full",
              connected ? "bg-emerald-500" : "bg-red-400"
            )}
            title={connected ? "WebSocket connected" : "Disconnected"}
          />
        </div>
      </header>

      {/* ── board ──────────────────────────────────────────────── */}
      <div className="grid flex-1 grid-cols-3 gap-4 overflow-auto">
        <Column status="queued" label="Queued" />
        <Column status="in_progress" label="In Progress" />
        <Column status="done" label="Done" />
      </div>

      <footer className="mt-4 text-center text-xs text-muted-foreground">
        Demo – AI ↔ Human orchestration
      </footer>
    </div>
  );
}

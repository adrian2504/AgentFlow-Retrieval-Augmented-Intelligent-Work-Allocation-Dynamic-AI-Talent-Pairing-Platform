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
  routedTo: "ai" | "human";
  owner: string;
};

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/tasks");
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      const data: Task | Task[] = JSON.parse(e.data);
      setTasks((prev) => {
        if (Array.isArray(data)) return data;
        return [...prev.filter((t) => t.id !== data.id), data];
      });
    };
    return () => ws.close();
  }, []);

  const byStatus = useCallback(
    (s: Task["status"]) => tasks.filter((t) => t.status === s),
    [tasks]
  );

  const Column = ({ status, label }: { status: Task["status"]; label: string }) => (
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
                  "border-2 cursor-pointer",
                  task.routedTo === "ai" ? "border-blue-400" : "border-emerald-400"
                )}
              >
                <CardContent className="p-3 flex items-center gap-3">
                  {task.routedTo === "ai" ? <Bot size={20} /> : <User2 size={20} />}
                  <div className="flex-1">
                    <p className="font-medium leading-tight line-clamp-2">{task.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {task.routedTo === "ai" ? "AI Agent: " : "Human: "}
                      {task.owner}
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

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    await fetch("http://localhost:8000/projects", { method: "POST", body: fd });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4 flex flex-col">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">AgentFlow Demo</h1>
        <div className="flex items-center gap-3">
          <input id="file" type="file" className="hidden" onChange={handleUpload} accept=".pdf,.md,.txt" />
          <label htmlFor="file">
            <Button variant="secondary">Upload Project Spec</Button>
          </label>
          <div
            className={cn("h-3 w-3 rounded-full", connected ? "bg-emerald-500" : "bg-red-400")}
            title={connected ? "Connected" : "Disconnected"}
          />
        </div>
      </header>
      <main className="flex flex-1 gap-4 overflow-x-auto">
        <Column status="queued" label="Queued" />
        <Column status="in_progress" label="In Progress" />
        <Column status="done" label="Done" />
      </main>
      <footer className="text-center text-xs text-muted-foreground mt-4">
        Demo – AI ↔ Human orchestration
      </footer>
    </div>
  );
}

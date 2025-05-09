import { useEffect, useState } from "react";
import type { Task } from "../types";

/**
 * Opens a WebSocket to the backend and keeps the task list live.
 * Falls back to ws://localhost:8000/ws/tasks when VITE_WS_URL is not set.
 */
export const useTasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // use env var if provided:  VITE_WS_URL=ws://backend:8000/ws/tasks
    const ws = new WebSocket(
      import.meta.env.VITE_WS_URL ?? "ws://localhost:8000/ws/tasks"
    );

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (ev) => {
      const incoming: Task[] = JSON.parse(ev.data);

      // merge by id so we don’t lose old fields (e.g. result)
      setTasks((prev) => {
        const map = new Map<string, Task>(prev.map((t) => [t.id, t]));
        for (const t of incoming) map.set(t.id, { ...map.get(t.id), ...t });
        return Array.from(map.values());
      });
    };

    return () => ws.close();
  }, []);

  return { tasks, connected };
};

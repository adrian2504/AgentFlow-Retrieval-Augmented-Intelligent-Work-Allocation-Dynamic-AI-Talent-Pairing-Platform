export type Task = {
    id: string;
    title: string;
    status: "queued" | "in_progress" | "done";
    routedTo: "ai" | "human";
    owner?: string;     // set for human tasks & AI agent name
    result?: string;    // filled once the task is finished
  };
  
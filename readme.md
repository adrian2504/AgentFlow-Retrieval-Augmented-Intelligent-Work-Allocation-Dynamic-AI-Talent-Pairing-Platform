# AgentFlow  
**Retrieval‑Augmented Intelligent Work Allocation & Dynamic AI‑Talent Pairing Platform**

---

## 🚀 What Is AgentFlow?

AgentFlow is a proof‑of‑concept system that **analyzes any project brief, breaks it into atomic tasks, and decides in real time whether each task should be handled by an AI agent or a human expert**.  
It then feeds both parties the right context (via RAG), orchestrates their hand‑offs, and streams live status updates to a responsive Kanban‑style dashboard.

---

## ✨ Key Capabilities

| Capability | How it works |
|------------|--------------|
| **Task Decomposition** | GPT‑powered splitter converts raw specs into structured task objects. |
| **Intelligent Routing** | Heuristic + ML / LLM rules decide **AI vs human** and pick an assignee based on skills & availability. |
| **RAG for Context** | pgvector‑backed store retrieves the top‑K docs; injected into prompts & human briefs. |
| **Orchestration Loop** | Async queue executes AI tasks (LLMs) or pings human workers; supports iterative review‑refine cycles. |
| **Live Dashboard** | React + Tailwind UI shows **Queued → In‑Progress → Done** columns with WebSocket updates. |
| **Pluggable Models** | Works with OpenAI GPT‑4o, Meta Llama‑3 (via vLLM/TGI), or any OpenAI‑compatible endpoint. |

---

## ✨ What’s Inside
* **Backend** – FastAPI, Chroma (in‑memory), Ollama‑served Phi‑3 mini (3.8 B) for chat + embeddings.
* **Frontend** – React + Vite + Tailwind Kanban board (live WebSocket updates).
* **No paid cloud** – Runs on local CPU, free RunPod CPU pod, or a Hugging Face Space.

---

## 🏛️ Layered Architecture Overview

The AgentFlow stack is organized into **four clear layers**, each with focused responsibilities.

#### 1. UI Layer
| Component | Responsibility |
|-----------|----------------|
| **Kanban Dashboard (React)** | Live board showing task cards moving through *Queued → In‑Progress → Done*. |
| **Task Management UI** | Edit, re‑assign, or re‑run tasks; view AI / human outputs. |
| **Project Brief Upload** | Drop‑zone for PDFs / Markdown / text specs that kick‑off analysis. |

---

#### 2. LLM Service Layer
| Component | Responsibility |
|-----------|----------------|
| **Ollama** | Local serving infrastructure exposing an **OpenAI‑compatible** REST endpoint. |
| **Meta Llama‑3‑8B‑Instruct** | Primary language model that powers task analysis and AI execution. |
| **OpenAI Compatibility Adapter** | Lets backend call `ChatCompletion` & `Embedding` endpoints without code changes. |

---

#### 3. Human Layer
| Role | Responsibility |
|------|----------------|
| **Experts** | Tackle complex, domain‑specific tasks the LLM shouldn’t handle. |
| **Reviewers** | Validate AI / expert work; request revisions if quality fails. |

---

#### 4. Service Layer
| Micro‑service | Key Functions |
|---------------|---------------|
| **Task Analyzer** | • Parse project brief<br>• Decompose into atomic tasks<br>• Map task dependencies |
| **Router** | • Decide *AI vs Human* per task<br>• Allocate resources / match skills |
| **Orchestrator** | • Schedule tasks<br>• Manage hand‑offs & retries<br>• Track status for UI & logs |
| **RAG System** | • Index docs in ChromaDB<br>• Retrieve top‑K context<br>• Enrich prompts & human briefs |
| **API Gateway** | • **FastAPI** endpoints (REST + WebSockets)<br>• CORS middleware for the React front‑end |

---

#### 5. Data Layer
| Store | Purpose |
|-------|---------|
| **Async Task Queue** | Buffers tasks for the orchestrator workers. |
| **ChromaDB (Vector Store)** | Stores Llama embeddings for similarity search in the RAG pipeline. |
| **Document Storage** | Holds raw project briefs, task outputs, and any supporting files. |




## 🛠️ Stack

| Layer | 	Tech | 
|------------|--------------|
| **API & WS**	| FastAPI, Uvicorn|
| **Queue / Async**	| Python asyncio (swap in Celery/Temporal) |
| **Vector Store**|	Postgres + pgvector (HNSW) |
|**LLM Serving** |	 vLLM / TGI + Meta Llama |
| **Front‑End**|	React, TailwindCSS, shadcn/ui, framer‑motion |
|**DevOps**| Docker Compose, dotenv| 


# 🧠 **Project Title: MemoHub**

**Tagline:** *Empowering AI Agents with Long-Term, Multi-Modal Memory — Built on NVIDIA NIM + AWS*

---

## 🚩 **Overview**

**MemoHub** is a multi-modal **memory engine** that transforms your everyday experiences — text, voice, images, and documents — into an evolving, structured stream of knowledge.
By organizing these "memory units" in a semantic graph, it provides **AI agents with long-term recall and reasoning capabilities**, enabling them to understand not only *what* you said, but *when*, *why*, and *in what context*.

Our vision: to bridge human-like memory and AI cognition through a unified system that can *remember, relate, and reason* over time — powered by **NVIDIA NIM** and **AWS infrastructure**.

---

## 💡 **Problem**

Most AI assistants today have **short-term memory** — they forget prior interactions, lose context, and can't build upon previous experiences.
Humans, by contrast, continuously integrate information from **multiple modalities** (speech, images, text, meetings).
This creates a cognitive gap between human memory and AI reasoning.

### Challenges we address

* Fragmented data across formats and platforms
* Lack of persistent, contextual AI memory
* Inefficient retrieval and reasoning over accumulated knowledge

---

## 🚀 **Solution**

**MemoHub** continuously collects and organizes multi-modal inputs into a **unified "memory stream"**, stored as structured **memory cells** with semantic metadata.

Each memory cell encodes:

* Content embeddings (text, image, audio transcripts)
* Context (timestamp, source, relational links)
* Summaries and topics for fast retrieval

During conversations or reasoning tasks, the **AI Agent** retrieves and reasons over related memory clusters using **NVIDIA NIM microservices**, allowing it to:

* Recall past events and visual cues
* Draw inferences based on long-term context
* Adapt dynamically through continuous learning

This transforms an agent from a reactive chatbot into a **cognitive, context-aware system** capable of reasoning over its own history.

---

## 🏆 **AWS & NVIDIA Hackathon Requirements**

This project fully complies with all hackathon requirements:

### ✅ Required Components Implemented

| Requirement | Implementation | Status |
|------------|----------------|---------|
| **LLM Reasoning Model** | NVIDIA NIM `llama-3.1-nemotron-nano-8B-v1` deployed as microservice | ✅ Implemented |
| **Retrieval Embedding NIM** | NVIDIA `llama-3.2-nv-embedqa-1b-v2` for semantic search | ✅ Implemented |
| **Deployment Platform** | Amazon EKS Cluster with GPU-enabled node groups (g5.2xlarge) | ✅ Implemented |
| **Agentic AI Application** | Memory-driven AI agent with RAG and multi-step reasoning | ✅ Implemented |

### 🔧 Technical Stack Alignment

* **NVIDIA NIM LLM Service**: Containerized `llama-3.1-nemotron-nano-8B-v1` on EKS for intelligent dialogue and reasoning
* **NVIDIA Retrieval NIM**: Embedding model for vector generation and semantic retrieval
* **AWS EKS**: Kubernetes orchestration with GPU node pools for scalable inference
* **AWS Services**: DynamoDB (memory metadata), S3 (file storage), EC2 (GPU compute)
* **Agentic Framework**: LangChain + custom orchestration for memory-augmented reasoning

---

## ⚙️ **Technical Architecture**

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                            │
│              Upload / Search / Organize / Chat                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                FastAPI Gateway (AWS EKS)                         │
│           Auth / API Keys / Uploads / Query Router              │
└───────────┬────────────────────────┬────────────────────────────┘
            │                        │
            ▼                        ▼
┌─────────────────────┐    ┌──────────────────────────────────────┐
│   Agentic Layer     │    │      NVIDIA NIM Services (EKS)       │
│   - Curator Agent   │◄───┤  - LLM NIM (llama-3.1-nemotron)     │
│   - Retriever Agent │    │  - Embedding NIM (nv-embedqa)        │
│   - Organizer Agent │    │  - Vision NIM (optional)             │
└──────────┬──────────┘    └──────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer (AWS)                            │
│  - DynamoDB (metadata + vectors)  - S3 (files)                  │
│  - PostgreSQL + pgvector (optional graph storage)               │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Layers

| Layer | Description | Technologies |
|-------|-------------|--------------|
| **Frontend Dashboard** | User interface for upload, search, organization, and AI chat | Next.js, TailwindCSS, Zustand |
| **API Gateway** | FastAPI orchestration, authentication, routing, file handling | FastAPI, JWT Auth, AWS EKS |
| **Agentic AI Layer** | **Core Innovation**: Memory-driven agents with multi-step reasoning using **llama-3.1-nemotron-nano-8B-v1 NIM** | NVIDIA NIM LLM, LangChain Agents, Custom Orchestration |
| **Retrieval & Embedding** | Semantic search and vector generation via **Retrieval Embedding NIM** | **NVIDIA NIM** `llama-3.2-nv-embedqa-1b-v2`, Cosine Similarity |
| **Memory Storage** | Structured memory units with embeddings, metadata, and relationships | AWS DynamoDB (vectors + metadata), PostgreSQL + pgvector |
| **File Storage** | Multi-modal file storage (PDFs, images, documents, audio) | AWS S3 with lifecycle policies |
| **Deployment Infrastructure** | **AWS EKS** cluster with NVIDIA GPU nodes for NIM workloads | Amazon EKS, EC2 g5.2xlarge instances, NVIDIA GPU Operator |

### Key Workflows

#### 1. **Upload Workflow**
```
User Upload → File Type Check → S3 Storage → 
Multi-Modal Parser → Text Extraction → 
Embedding Generation (NIM) → DynamoDB Storage → 
Memory Index Update
```

#### 2. **Search Workflow**
```
User Query → Query Embedding (NIM) → 
Semantic Search (Cosine Similarity) → 
Ranking & Filtering → Result Return
```

#### 3. **AI Conversation Workflow**
```
User Question → Search Related Memory (Retriever Agent) → 
Context Building → LLM Reasoning (NIM) → 
Response Generation → Memory Update
```

---

## 🧩 **Key Features**

1. 🎙️ **Multi-Modal Capture** – Upload or record voice, images, PDFs, or text to build a continuous knowledge timeline.
2. 🧠 **Long-Term Memory Agent** – AI recalls user-specific sessions, entities, and preferences across conversations.
3. 🔍 **Semantic Search & Q/A** – Ask *"What insights did I discuss in last week's meeting?"* and get contextual answers.
4. 🤖 **Agentic Reasoning** – Multi-agent system orchestrates retrieval, context building, and intelligent response generation.
5. 🔁 **Continuous Learning Loop** – New interactions strengthen or reshape existing memory nodes, inspired by human cognition.
6. 🔐 **User Authentication** – Secure JWT-based authentication with API key management for external integrations.
7. 🌐 **API Access** – RESTful API allows external LLMs and applications to query user memories.

---

## ⚡ **Innovation**

* **Native NVIDIA NIM Integration**: Built from the ground up on NVIDIA NIM microservices for both embeddings and LLM inference
* **Memory-Augmented Agentic AI**: Goes beyond simple RAG – implements multi-agent orchestration with memory consolidation
* **Scalable GPU Infrastructure**: Deployed on AWS EKS with auto-scaling GPU node groups for cost-effective inference
* **Multi-Modal Processing**: Handles text, PDFs, images, and audio transcripts in a unified memory stream
* **Memory Consolidation**: Mimics human memory by prioritizing relevant experiences while allowing others to fade
* **Production-Ready Architecture**: Full deployment pipeline with Kubernetes, Helm charts, and monitoring

---

## 🌍 **Impact**

* **For Individuals:** A personal AI memory companion that never forgets — enabling deep contextual assistance across time and providing continuity in AI interactions.
* **For Teams:** A shared, searchable knowledge stream that captures conversations, notes, and visual data — becoming an institutional memory.
* **For AI Agents:** A foundation for genuine *contextual intelligence* — transforming reactive chatbots into cognitive systems with memory-driven reasoning and decision-making.
* **For Developers:** An API-first architecture allowing external LLMs to leverage user memories through secure, rate-limited access.

---

## 🚀 **Deployment**

### Development Environment
- NVIDIA API endpoints for rapid prototyping
- Local DynamoDB and S3 simulation

### Production Environment (AWS EKS)
- NVIDIA NIM containers deployed on GPU-enabled EKS nodes
- Auto-scaling based on inference load
- Multi-AZ deployment for high availability
- CloudWatch monitoring and logging
- Complete Kubernetes manifests and Helm charts included

**See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.**

---

## 📚 **Documentation**

- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Complete deployment guide for AWS EKS with NVIDIA NIM
- **[API Documentation](http://localhost:8000/docs)**: Interactive Swagger UI with all endpoints
- **Architecture Diagrams**: System and workflow visualizations included in repository

---

## 🔗 **Repository Structure**

```
MemoHub/
├── main.py                 # FastAPI application entry point
├── routers/                # API route handlers
│   ├── upload.py          # File upload endpoints
│   ├── search.py          # Semantic search APIs
│   ├── ai_agent.py        # AI chat and reasoning
│   └── auth.py            # Authentication
├── services/               # Core business logic
│   ├── embedding_service.py   # NVIDIA NIM embedding integration
│   ├── llm_service.py         # NVIDIA NIM LLM integration
│   ├── database_service.py    # DynamoDB operations
│   └── ai_agent_service.py    # Agentic orchestration
├── UI/memohub/             # Next.js frontend
├── DEPLOYMENT.md           # AWS EKS deployment guide
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## 🏁 **In Summary**

> **MemoHub** transforms scattered experiences into a living knowledge fabric — empowering AI agents to remember, reason, and evolve.
>
> Built with **NVIDIA NIM microservices** (`llama-3.1-nemotron-nano-8B-v1` for reasoning, `llama-3.2-nv-embedqa-1b-v2` for embeddings) and deployed on **AWS EKS** with GPU acceleration for scalable, production-grade agentic AI.

---

## 🏆 **AWS & NVIDIA Hackathon Submission**

This project represents a complete implementation of an Agentic AI application meeting all hackathon requirements:
- ✅ Uses `llama-3.1-nemotron-nano-8B-v1` as LLM reasoning model
- ✅ Implements Retrieval Embedding NIM for semantic search
- ✅ Deployed on AWS EKS with GPU node groups
- ✅ Demonstrates practical value with memory-driven AI interactions
- ✅ Production-ready with authentication, API management, and monitoring

**Demo Video**: [(https://youtu.be/0-zydyh3uoE)]  
**GitHub Repository**: [(https://github.com/fc9399/MemoHub)]

## 🙏 **Credits & Acknowledgments**

### Team Members
- **[Yunlan Qiao]** - Lead Developer, Frontend Architecture
- **[Lin Jia]** - AI/ML Engineering, NIM Integration, Backend Architecture
- **[Fung Chau]** - Backend Development, Testing

---

**Built with ❤️ for the AWS & NVIDIA Hackathon 2025**

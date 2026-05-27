# FinMate - Architecture

## System Overview

FinMate is an AI-powered personal finance assistant that analyzes spending data and provides personalized financial guidance through a conversational interface.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STREAMLIT FRONTEND                            │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ Chat UI  │  │ File Upload  │  │ Dashboard │  │ Metrics View │  │
│  └────┬─────┘  └──────┬───────┘  └─────┬─────┘  └──────────────┘  │
└───────┼────────────────┼────────────────┼──────────────────────────┘
        │                │                │
        ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GUARDRAILS LAYER                                │
│  ┌─────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │ PII Filter  │  │ Injection Detect │  │ Domain Enforcement   │  │
│  └─────────────┘  └──────────────────┘  └──────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH ORCHESTRATION                           │
│                                                                      │
│  ┌──────────────┐     ┌───────────────────┐                        │
│  │  Classify    │────▶│  Retrieve Context  │                        │
│  │  Intent      │     │  (RAG Pipeline)    │                        │
│  └──────────────┘     └────────┬──────────┘                        │
│                                 │                                    │
│                    ┌────────────┼────────────────┐                  │
│                    ▼            ▼                 ▼                  │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐     │
│  │   Budget     │  │    Savings       │  │   Spending       │     │
│  │  Analysis    │  │    Advice        │  │   Insights       │     │
│  └──────────────┘  └──────────────────┘  └──────────────────┘     │
│                    ▼                              ▼                  │
│  ┌──────────────┐                    ┌──────────────────┐          │
│  │ Goal Setting │                    │   General Q&A    │          │
│  │ (Human Loop) │                    │                  │          │
│  └──────────────┘                    └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
        │                                            │
        ▼                                            ▼
┌────────────────────┐                  ┌────────────────────────────┐
│   MCP SERVER       │                  │     RAG PIPELINE           │
│  ┌──────────────┐  │                  │  ┌─────────────────────┐  │
│  │ Categorize   │  │                  │  │ Knowledge Base (MD) │  │
│  │ Expenses     │  │                  │  └──────────┬──────────┘  │
│  ├──────────────┤  │                  │             ▼             │
│  │ Calculate    │  │                  │  ┌─────────────────────┐  │
│  │ Budget       │  │                  │  │ Text Splitter       │  │
│  ├──────────────┤  │                  │  │ (800 chars, 200 ov) │  │
│  │ Savings      │  │                  │  └──────────┬──────────┘  │
│  │ Plan         │  │                  │             ▼             │
│  └──────────────┘  │                  │  ┌─────────────────────┐  │
└────────────────────┘                  │  │ OpenAI Embeddings   │  │
                                        │  │ (text-embed-3-small)│  │
        │                               │  └──────────┬──────────┘  │
        ▼                               │             ▼             │
┌────────────────────────────┐         │  ┌─────────────────────┐  │
│    DOCUMENT PARSERS        │         │  │ ChromaDB (Local)    │  │
│  ┌───────┐ ┌────┐ ┌─────┐│         │  │ MMR Retrieval       │  │
│  │  CSV  │ │PDF │ │Image││         │  └─────────────────────┘  │
│  │Parser │ │ "" │ │OCR  ││         └────────────────────────────┘
│  └───────┘ └────┘ └─────┘│
└────────────────────────────┘                       │
                                                     ▼
                                        ┌────────────────────────────┐
                                        │      MONITORING            │
                                        │  ┌─────────────────────┐  │
                                        │  │ LangSmith Tracing   │  │
                                        │  │ - All LLM calls     │  │
                                        │  │ - Latency tracking  │  │
                                        │  │ - Token usage       │  │
                                        │  └─────────────────────┘  │
                                        └────────────────────────────┘
```

## Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| LLM | GPT-4o / GPT-4o-mini | Best balance of quality, speed, and cost for financial analysis |
| Orchestration | LangGraph | Most flexible for conditional routing and state management |
| Vector DB | ChromaDB | Zero-config, local persistence, sufficient for our document count |
| Embeddings | text-embedding-3-small | Cost-effective ($0.02/1M tokens), 1536 dims, strong retrieval |
| Frontend | Streamlit | Rapid prototyping, built-in chat UI, file upload support |
| Monitoring | LangSmith | Native LangChain integration, free tier sufficient |
| Guardrails | Custom (regex + rules) | Lightweight, no external dependencies, focused on PII |

## Data Flow (Single Request)

1. User sends message via Streamlit chat
2. Guardrails validate input (PII masking, injection detection)
3. LangGraph entry: Intent Classification (GPT-4o, temp=0)
4. RAG retrieval: Query enhanced with intent, MMR search in ChromaDB
5. Route to specialist node based on classified intent
6. Specialist generates response using context + transaction data + profile
7. Guardrails validate output (PII masking, disclaimer injection)
8. Response rendered in chat with intent badge
9. Full trace logged to LangSmith

## Key Design Decisions

### Why LangGraph over CrewAI?
- More granular control over routing logic
- Native support for conditional edges and state management
- Better suited for single-agent-multiple-roles pattern
- Easier to debug with explicit graph visualization

### Why ChromaDB over Pinecone/Qdrant?
- Zero infrastructure cost for demo
- Local persistence sufficient for our knowledge base (~50 chunks)
- No network latency for retrieval
- Easy to rebuild from source documents

### Why GPT-4o as primary model?
- Superior instruction following for financial analysis
- Best vision capabilities for receipt OCR
- Acceptable latency (~1-2s) for conversational use
- GPT-4o-mini as fallback for cost-sensitive operations (intent classification)

### Chunking Strategy
- 800 character chunks with 200 overlap
- Markdown-aware splitting (headers first, then paragraphs)
- Preserves section context while keeping retrieval precise
- Overlap prevents losing information at chunk boundaries

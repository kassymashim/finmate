# FinMate - AI-Powered Personal Finance Assistant

> An intelligent personal finance assistant that analyzes spending data and provides personalized budgeting insights, savings recommendations, and financial guidance through a conversational chatbot interface.

## Problem Statement

Many people struggle to understand their spending habits and make informed financial decisions. FinMate turns transaction data into simple, personalized, and actionable financial advice.

## Features

- **Conversational Finance Advisor** - Natural language chat about budgeting, savings, and spending
- **Transaction Analysis** - Upload CSV/PDF bank statements for automated categorization
- **Receipt OCR** - Take photos of receipts for instant expense tracking (GPT-4o Vision)
- **Personalized Budgets** - 50/30/20 rule adapted to your specific situation
- **Savings Planning** - Milestone-based plans with timelines and action items
- **Spending Insights** - Pattern detection, anomaly alerts, benchmark comparisons
- **Financial Knowledge RAG** - Answers grounded in curated financial best practices

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for full system design and diagrams.

**Tech Stack:**
- **LLM**: OpenAI GPT-4o (primary) + GPT-4o-mini (fallback)
- **Orchestration**: LangGraph (multi-step workflow with intent routing)
- **Vector DB**: ChromaDB (local, persistent)
- **Embeddings**: OpenAI text-embedding-3-small
- **Frontend**: Streamlit
- **Monitoring**: LangSmith
- **Guardrails**: Custom PII filtering + prompt injection detection

## Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- LangSmith API key (free at https://smith.langchain.com)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd finmate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run

```bash
# One-command launch (generates data + builds RAG + starts app)
python run.py
```

Or step-by-step:
```bash
# Generate synthetic data
python -m backend.utils.generate_synthetic_data

# Build knowledge base
python -m backend.rag.knowledge_rag

# Launch Streamlit
streamlit run frontend/app.py
```

### Docker

```bash
docker-compose up --build
```

## Evaluation

See [EVALS.md](EVALS.md) for complete evaluation results and methodology.

```bash
# Quick eval
python -m backend.evals.run_evals --quick

# Full eval with LLM-as-Judge
python -m backend.evals.run_evals --full

# A/B Test
python -m backend.evals.run_evals --ab
```

## Project Structure

```
finmate/
├── backend/
│   ├── agents/          # LangGraph workflow and orchestration
│   ├── mcp_server/      # Custom MCP server with finance tools
│   ├── rag/             # RAG pipeline (ChromaDB + embeddings)
│   ├── evals/           # Golden dataset + evaluation scripts
│   ├── parsers/         # PDF, CSV, image document parsers
│   └── utils/           # Config, guardrails, data generation
├── frontend/            # Streamlit application
├── skills/              # Custom Skill (SKILL.md)
├── data/
│   ├── knowledge_base/  # Financial knowledge documents
│   └── sample_transactions/  # Synthetic demo data
├── docs/                # Additional documentation
├── ARCHITECTURE.md      # System architecture
├── EVALS.md            # Evaluation results
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## MCP Server

Custom MCP server providing 3 financial tools:
1. **categorize_expenses** - Auto-categorize transactions by merchant
2. **calculate_budget** - Generate personalized budget allocation
3. **get_savings_plan** - Create milestone-based savings plans

## Key Decisions & Trade-offs

| Decision | Rationale |
|----------|-----------|
| GPT-4o over Claude | Better vision capabilities for receipt OCR, consistent JSON output |
| ChromaDB over Pinecone | Zero cost, local persistence, sufficient for demo scale |
| LangGraph over CrewAI | More granular routing control, better state management |
| Streamlit over Next.js | 5x faster development, built-in chat/upload components |
| text-embedding-3-small | Best cost/quality ratio for retrieval at $0.02/1M tokens |

## Demo

**Live Demo**: [URL if deployed]

**Demo Script**:
1. Load sample data (6 months of transactions for "Alex Johnson")
2. Ask "Where is my money going?" → Spending breakdown with insights
3. Ask "How can I save for a $15,000 down payment?" → Personalized savings plan
4. Upload a receipt image → OCR analysis and categorization
5. Show LangSmith dashboard with real traces

## Author

LLM Engineering Course - Final Project 2026

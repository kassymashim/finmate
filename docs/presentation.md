# FinMate - Presentation Slides
## AI-Powered Personal Finance Assistant
### LLM Engineering Course - Final Project | May 2026

---

## Slide 1: Title

**FinMate**
*AI-Powered Personal Finance Assistant*

LLM Engineering Course — Final Project
May 2026

GitHub: github.com/kassymashim/finmate

---

## Slide 2: The Problem

**People struggle to understand where their money goes.**

- 65% of Americans don't know how much they spent last month
- Tracking expenses manually is tedious → people give up
- Generic budgeting advice doesn't account for individual patterns
- Existing apps show data but don't provide actionable guidance

**Current solutions:** Spreadsheets (boring), banking apps (show data, no advice), financial advisors (expensive)

---

## Slide 3: The Solution — FinMate

**An AI assistant that turns transaction data into personalized financial advice.**

- Real-time spending dashboard with visual analytics
- Conversational AI that knows YOUR spending patterns
- Quick expense logging: type "Chipotle $15" → instant categorization
- Receipt scanning with computer vision (OCR)
- Personalized budgets, savings plans, and goal tracking

**Target user:** Young professionals (25-35) who want to manage money better but find traditional budgeting apps boring or overwhelming.

---

## Slide 4: Live Demo

**Demo Flow:**
1. Dashboard — spending breakdown by category, monthly trends
2. Month filter — switch between months to compare
3. Quick add expense — "Starbucks $6" → added to Restaurants
4. AI Chat — "Where is my money going?" → personalized analysis
5. AI Chat — "How can I save $15,000?" → milestone plan
6. Receipt upload → GPT-4o Vision extracts data
7. LangSmith — show real traces of the conversation

---

## Slide 5: Architecture Overview

```
User → Next.js Frontend → FastAPI Backend
                              ↓
                    Guardrails (PII filter, injection detection)
                              ↓
                    LangGraph Orchestration
                    ├── Classify Intent (GPT-4o, temp=0)
                    ├── Retrieve Context (ChromaDB RAG)
                    └── Route to Specialist:
                        ├── Budget Analysis
                        ├── Savings Advice
                        ├── Spending Insights
                        ├── Goal Setting (human-in-the-loop)
                        └── General Q&A
                              ↓
                    LangSmith (tracing all calls)
```

**Tech Stack:** LangGraph | GPT-4o | ChromaDB | Next.js | FastAPI | LangSmith

---

## Slide 6: LangGraph Workflow

**Why LangGraph over CrewAI/Parlant?**
- More granular control over routing logic
- Native conditional edges and state management
- Better for single-agent-multiple-roles pattern
- Easier to debug with explicit graph structure

**Workflow:**
1. **Intent Classification** → Determines what user needs (budget/savings/spending/goals/general)
2. **RAG Retrieval** → Fetches relevant financial knowledge (MMR search)
3. **Conditional Routing** → Routes to specialist handler based on intent
4. **Response Generation** → Personalized response using context + transaction data
5. **Human-in-the-loop** → Goal setting requires user confirmation

---

## Slide 7: RAG Pipeline & MCP Server

**RAG Pipeline:**
- Knowledge base: 4 curated financial documents (budgeting, savings, spending, goals)
- Chunking: 800 chars, 200 overlap, markdown-aware splitting
- Embeddings: OpenAI text-embedding-3-small ($0.02/1M tokens)
- Vector DB: ChromaDB (local, zero-config)
- Retrieval: MMR (λ=0.7) for diversity in results

**Custom MCP Server (3 tools):**
1. `categorize_expenses` — Auto-categorize transactions by merchant name
2. `calculate_budget` — 50/30/20 allocation with personalized adjustments
3. `get_savings_plan` — Milestone-based plan with timeline and action items

---

## Slide 8: Multimodality & Guardrails

**Multimodality — GPT-4o Vision:**
- Upload receipt/bank statement photos
- Extracts: merchant, date, items, total, category
- Structured JSON output for integration with dashboard
- Supports receipts, invoices, bank statement screenshots

**Guardrails:**
- PII Detection: Credit cards, SSNs, account numbers auto-masked
- Prompt Injection Detection: Blocks override attempts
- Domain Enforcement: Keeps responses within personal finance
- Output Validation: Adds disclaimers for investment-related content

---

## Slide 9: Evaluation Results

**Golden Dataset:** 35 examples across 5 intent categories

| Metric | Score |
|--------|-------|
| Intent Classification Accuracy | **80%** |
| Response Relevance (LLM-as-Judge) | **3.93 / 5.0** |
| Keyword Faithfulness | **92.2%** |
| Average Latency | **5.56s** |

**A/B Test: GPT-4o vs GPT-4o-mini**
- GPT-4o: Better quality (80% accuracy, 3.93 relevance)
- GPT-4o-mini: 10x cheaper, 2x faster, ~72% accuracy
- **Decision:** GPT-4o for responses (quality matters for financial advice), GPT-4o-mini for intent classification

**Misclassification Analysis:** 3/15 errors were boundary cases (spending_insights ↔ budget_analysis) — both valid handlers, no critical failures.

---

## Slide 10: LLM Choice & Hyperparameters

**Why GPT-4o?**
- Best vision capabilities for receipt OCR
- Superior instruction following for financial analysis
- Consistent structured JSON output
- Acceptable latency (~5.5s) for conversational use
- Fallback: GPT-4o-mini for cost-sensitive operations

**Hyperparameter Experiments:**
| Parameter | Tested Values | Selected | Rationale |
|-----------|--------------|----------|-----------|
| Temperature | 0.0, 0.3, 0.7, 1.0 | **0.3** | Consistent yet natural |
| Top-P | 0.8, 0.9, 1.0 | **0.9** | Reduces unlikely tokens |
| Max Tokens | 1024, 2048, 4096 | **2048** | Sufficient for detailed breakdowns |

**Cost per query:** ~$0.01 (acceptable for personal finance tool)

---

## Slide 11: Monitoring — LangSmith

**All LLM calls traced in LangSmith:**
- Intent classification calls
- RAG retrieval queries
- Response generation
- Receipt image analysis
- Token usage and latency per call

**What we track:**
- End-to-end latency per request
- Token consumption (input/output)
- Error rates and failure modes
- Cost per conversation

*[Show live LangSmith dashboard during demo]*

---

## Slide 12: Key Design Decisions & Trade-offs

| Decision | Why | Trade-off |
|----------|-----|-----------|
| LangGraph over CrewAI | Granular routing control | More boilerplate code |
| ChromaDB over Pinecone | Zero cost, local | Not production-scalable |
| GPT-4o over Claude | Better vision + JSON output | Higher cost per call |
| Next.js over Streamlit | Professional UI, full control | Longer dev time |
| 800-char chunks | Balance context vs precision | May split related info |

**Hypotheses that didn't hold:**
- "GPT-4o-mini is good enough for all tasks" → Quality dropped noticeably for financial advice
- "Users always phrase questions clearly" → Needed robust intent classification with overlap handling

---

## Slide 13: What's Next

**If continuing development:**
- Real bank API integration (Plaid) for live transaction sync
- Voice interface (audio-to-audio for hands-free expense logging)
- Fine-tuning on financial advisor conversations
- Multi-user auth with personalized profiles
- Mobile app (React Native)
- Deployed to production (Railway/Vercel)

**Business potential:**
- Freemium model: Free dashboard, premium AI advice
- Target: 25-35 year olds, first jobs, want financial literacy
- Differentiator: Conversational AI that knows YOUR patterns (not generic advice)

---

## Slide 14: Summary

**FinMate solves:** People can't easily understand and optimize their spending

**How:** AI-powered analysis + conversational guidance + visual dashboard

**Technical highlights:**
- LangGraph multi-step workflow with 5 specialist nodes
- RAG grounded in curated financial knowledge
- GPT-4o Vision for receipt OCR
- 80% intent accuracy, 3.93/5.0 response relevance
- Full observability via LangSmith

**GitHub:** github.com/kassymashim/finmate

---

## Slide 15: Q&A

**Thank you!**

Ready for questions.

---

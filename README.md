# B2B Multi-Agent Supply Negotiation

An autonomous multi-agent AI system that negotiates supply chain contracts between companies — without constant human intervention.

## Overview

Three specialized AI agents represent different business functions and negotiate directly with each other:

```
┌──────────────────────────────────────────────────────────┐
│                  NEGOTIATION ORCHESTRATOR                 │
│                     (LangGraph)                          │
│                                                          │
│  ┌─────────────┐    offers/counters    ┌──────────────┐  │
│  │ BUYER AGENT │ ◄──────────────────► │ SELLER AGENT │  │
│  │  AcmeCorp   │                      │ GlobalSupply  │  │
│  └──────┬──────┘                      └──────┬───────┘  │
│         │          agreement reached         │           │
│         └──────────────┬───────────────────┘           │
│                        ▼                                 │
│               ┌─────────────────┐                       │
│               │   LEGAL AGENT   │                       │
│               │   Compliance    │                       │
│               └─────────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

### Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Buyer** | Detects shortages, evaluates offers, counters or accepts | `check_inventory`, `predict_shortage`, `get_reference_price`, `evaluate_seller_offer` |
| **Seller** | Evaluates capacity, generates dynamic offers based on volume | `check_production_capacity`, `calculate_min_price`, `calculate_offer_price`, `evaluate_buyer_counter` |
| **Legal** | Reviews contracts for tariff, carbon, and payment compliance | `validate_incoterm`, `check_applicable_tariffs`, `check_carbon_compliance`, `validate_payment_terms`, `check_contract_clauses` |

### Negotiation Flow

```
Inventory Alert → Seller Initial Offer → Buyer Evaluates
     └── Accept ──────────────────────────────► Legal Review ──► Contract
     └── Counter ──► Seller Responds ──► Buyer Evaluates ──► (loop)
     └── Reject / Max Rounds ──────────────────────────────► Escalate
```

## Requirements

- Python 3.11+
- [Ollama](https://ollama.ai) running locally (default), or an API key for another provider

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd b2b-multiagent-supply-negotiation

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env to set your provider and API keys

# 5. (Ollama only) Pull a model
ollama pull llama3.2
```

## Configuration

Copy `.env.example` to `.env` and set your provider:

```env
# Default: Ollama (free, local, no API key needed)
PROVIDER=ollama
OLLAMA_MODEL=llama3.2

# Or: OpenAI
# PROVIDER=openai
# OPENAI_API_KEY=sk-...

# Or: Anthropic
# PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Or: Groq (fast, free tier available)
# PROVIDER=groq
# GROQ_API_KEY=gsk_...

# Or: Google Gemini
# PROVIDER=gemini
# GOOGLE_API_KEY=AIza...
```

## Running

```bash
python main.py
```

Example output:
```
============================================================
  B2B MULTI-AGENT SUPPLY NEGOTIATION SYSTEM
============================================================
  Provider  : OLLAMA
  Buyer     : AcmeCorp Manufacturing
  Seller    : GlobalSupplyCo
============================================================

[ALERT] Inventory shortage detected:
  Material       : hot_rolled_steel
  Current stock  : 150.0 metric_ton
  Reorder point  : 250.0 metric_ton
  Days remaining : -27.8
  Order quantity : 540.0 metric_ton

[START] Launching autonomous negotiation...
------------------------------------------------------------

  [Round 1] status=negotiating  | latest offer from seller: 724.35 EUR
  [Round 2] status=negotiating  | latest offer from buyer:  698.4 EUR
  [Round 3] status=agreed       | latest offer from seller: 711.5 EUR

============================================================
  NEGOTIATION RESULT
============================================================
  Status  : FINALIZED
  Rounds  : 3
  Contract: CTR-20260528-A1B2
  Value   : 384,210.00 EUR
  Verdict : APPROVED
============================================================
```

## Project Structure

```
├── src/
│   ├── agents/          # Buyer, Seller, Legal agent nodes
│   ├── models/          # Pydantic data models
│   ├── orchestrator/    # LangGraph state + graph
│   ├── providers/       # LLM factory (multi-provider)
│   ├── tools/           # LangChain tools for each agent
│   └── utils.py         # JSON parsing, ID generation
├── data/
│   ├── buyer_inventory.json   # AcmeCorp's stock levels
│   ├── seller_capacity.json   # GlobalSupplyCo's production
│   └── regulations.json       # Tariffs, carbon limits, payment rules
├── config.py            # Pydantic settings (env-driven)
├── main.py              # Entry point
└── requirements.txt
```

## Multi-Provider Support

The system works with any of these LLM providers — switch by changing `PROVIDER` in `.env`:

| Provider | Notes |
|----------|-------|
| **Ollama** | Default. Free, local, private. Needs Ollama installed. |
| **OpenAI** | GPT-4o-mini by default. Fast and affordable. |
| **Anthropic** | Claude Haiku by default. Good at structured output. |
| **Groq** | Free tier available. Very fast inference. |
| **Gemini** | Google's model. Free tier available. |

## Customization

### Add a new material

Edit [`data/buyer_inventory.json`](data/buyer_inventory.json) and [`data/seller_capacity.json`](data/seller_capacity.json) to add materials.

### Adjust negotiation parameters

Edit `.env`:
```env
MAX_ROUNDS=15          # Maximum negotiation rounds before escalation
BUYER_COMPANY=MyCompany
SELLER_COMPANY=TheirCompany
```

### Add a new LLM provider

Add a new `case` to [`src/providers/llm.py`](src/providers/llm.py) and install the corresponding `langchain-<provider>` package.

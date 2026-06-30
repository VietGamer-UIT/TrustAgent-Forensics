<p align="center">
  <h1 align="center">🛡️ TrustAgent.Forensics</h1>
  <p align="center">
    <strong>Neuro-Symbolic AI Governance Platform</strong><br/>
    <em>Formal Verification for AI Agent Actions using Z3 Theorem Prover</em>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"/>
    <img src="https://img.shields.io/badge/Z3-4.16.0-orange.svg" alt="Z3 4.16"/>
    <img src="https://img.shields.io/badge/Gemini-2.0_Flash-4285F4.svg" alt="Gemini 2.0"/>
    <img src="https://img.shields.io/badge/LangGraph-0.4+-purple.svg" alt="LangGraph 0.4+"/>
    <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI 0.115+"/>
    <img src="https://img.shields.io/badge/PostgreSQL-17-336791.svg" alt="PostgreSQL 17"/>
    <img src="https://img.shields.io/badge/INNOSTAR-2026-red.svg" alt="INNOSTAR 2026"/>
  </p>
</p>

---

## 🎯 What is TrustAgent.Forensics?

**TrustAgent.Forensics** is a Neuro-Symbolic AI Governance platform that creates a mathematical "guardrail" layer to verify every action taken by autonomous AI Agents **before execution**.

Instead of relying on probabilistic prompt engineering (which can be bypassed by prompt injection), we use **Z3 Theorem Prover** (SMT Solver by Microsoft Research) to provide **deterministic, mathematically-proven** compliance verification — making AI decisions auditable, trustworthy, and legally compliant.

### 🧠 The AI Governance Gap

Modern AI Agents are moving from *Copilots* (assistants) to *Autopilots* (autonomous actors). When AI makes financial, legal, or operational decisions autonomously, a single hallucination can cost millions. TrustAgent.Forensics solves this with a two-layer architecture:

```
User Request (Natural Language)
         │
    ┌────▼─────────────────────┐
    │  🧠 NEURAL LAYER          │  ← Gemini 2.0 Flash
    │   Semantic Parser         │     Understands ambiguous language
    │   "Strips" meaning        │     Returns structured JSON
    └────┬─────────────────────┘
         │ {amount: 25M, method: "cash"}
    ┌────▼─────────────────────┐
    │  ⚖️  SYMBOLIC LAYER       │  ← Z3 Theorem Prover (Microsoft)
    │  Formal Verifier          │     Mathematical proof, deterministic
    │  SAT / UNSAT              │     Cannot be fooled by language tricks
    └────┬─────────────────────┘
         │
    ┌────▼─────────────────────┐
    │  📋 FORENSICS LAYER       │  ← PostgreSQL 17 (JSONB)
    │  Immutable Audit Trail    │     Every decision logged permanently
    └──────────────────────────┘
```

### 🏆 INNOSTAR 2026

Developed for **INNOSTAR 2026 Student Startup Competition** — *"Applying Science & Technology in Business for the Digital Age"*.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+

### Installation

```bash
# Clone
git clone https://github.com/VietGamer-UIT/TrustAgent-Forensics.git
cd TrustAgent-Forensics

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install Phase 1 dependencies
pip install -r requirements.txt

# Copy env config
cp .env.example .env
```

### Run Tests

```bash
pytest tests/ -v
```

Expected:
```
26 passed in ~0.30s ✅
```

### Run API Server (Phase 4+)

```bash
uvicorn src.main:app --reload
# Open: http://localhost:8000/docs
```

---

## 📁 Project Structure

```
TrustAgent-Forensics/
├── src/
│   ├── config.py               # Settings & environment config
│   ├── z3_engine/              # ✅ Phase 1: Z3 Formal Verification Engine
│   │   ├── solver.py           # TrustAgentSolver — main Z3 wrapper
│   │   ├── models.py           # Pydantic data models
│   │   └── rules/              # Business rule definitions
│   │       ├── base_rule.py    # Abstract base class (Strategy pattern)
│   │       ├── vn_tax_rule.py  # 🇻🇳 Circular 96/2015 (20M VND cash rule)
│   │       └── kr_refund_rule.py # 🇰🇷 Tax refund (30K/75K KRW thresholds)
│   ├── semantic/               # 🔜 Phase 2: Gemini Semantic Parser
│   ├── agents/                 # 🔜 Phase 3: LangGraph Multi-Agent
│   ├── api/                    # 🔜 Phase 4: FastAPI REST endpoints
│   ├── database/               # 🔜 Phase 4: PostgreSQL Audit Trail
│   └── dashboard/              # 🔜 Phase 5: Web Dashboard UI
├── tests/
│   └── test_z3_engine.py       # 26 unit tests (Phase 1)
└── docs/
```

---

## ⚖️ Business Rules (Phase 1)

### 🇻🇳 Vietnamese Tax Rule — Circular 96/2015/TT-BTC

> *"Any purchase ≥ 20,000,000 VND must use non-cash payment to be tax-deductible"*

```python
# Z3 encoding: deterministic math, not a prompt
Implies(amount >= 20_000_000, Not(is_cash_payment))
```

| Scenario | Amount | Method | Result |
|----------|--------|--------|--------|
| Cash 25M for event | 25,000,000 VND | Cash | ❌ UNSAT — BLOCKED |
| Transfer 30M equipment | 30,000,000 VND | Bank transfer | ✅ SAT — ALLOWED |
| Cash 15M stationery | 15,000,000 VND | Cash | ✅ SAT — ALLOWED |

### 🇰🇷 Korean Tax Refund — Incheon Airport

> *"Receipts ≥ 30,000 KRW qualify. Refunds ≥ 75,000 KRW require customs inspection."*

```python
solver.add(is_eligible == (receipt_amount >= 30_000))
solver.add(Implies(refund_amount < 75_000,  Not(needs_customs_check)))
solver.add(Implies(refund_amount >= 75_000, needs_customs_check))
```

---

## 🔧 Tech Stack (2026)

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Neural** | Google Gemini | 2.0 Flash | NL → structured JSON parsing |
| **Symbolic** | Z3 Theorem Prover | 4.16.0 | Deterministic compliance proof |
| **Orchestration** | LangGraph | 0.4+ | Multi-agent workflow + self-correction |
| **Backend** | FastAPI | 0.115+ | Async REST API server |
| **Database** | PostgreSQL | 17 (JSONB) | Immutable forensic audit trail |
| **Validation** | Pydantic | v2 | Schema enforcement |
| **Deployment** | Docker | 27+ | Containerized deployment |
| **Testing** | pytest | 9.x | Unit & integration tests |

---

## 🗺️ Development Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| **v0.1** | Z3 Verification Engine + Business Rules | ✅ Done |
| **v0.2** | Gemini Semantic Parser (NL → JSON) | 🔄 In Progress |
| **v0.3** | LangGraph Multi-Agent + Self-Correction Loop | 🔜 Planned |
| **v0.4** | FastAPI Backend + PostgreSQL Audit Trail | 🔜 Planned |
| **v0.5** | Dashboard Frontend | 🔜 Planned |
| **v1.0** | Docker + Demo Package (INNOSTAR Submission) | 🔜 Planned |

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

<p align="center">
  <h1 align="center">🛡️ TrustAgent.Forensics</h1>
  <p align="center">
    <strong>Neuro-Symbolic AI Governance Platform</strong><br/>
    <em>Formal Verification for AI Agent Actions using Z3 Theorem Prover</em>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"/>
    <img src="https://img.shields.io/badge/Z3-Theorem_Prover-orange.svg" alt="Z3"/>
    <img src="https://img.shields.io/badge/FastAPI-0.110+-green.svg" alt="FastAPI"/>
    <img src="https://img.shields.io/badge/LangGraph-Multi_Agent-purple.svg" alt="LangGraph"/>
    <img src="https://img.shields.io/badge/INNOSTAR-2026-red.svg" alt="INNOSTAR 2026"/>
  </p>
</p>

---

## 🎯 What is TrustAgent.Forensics?

**TrustAgent.Forensics** is a Neuro-Symbolic AI Governance platform that creates a mathematical "guardrail" layer to verify every action taken by autonomous AI Agents before execution.

Instead of relying on probabilistic prompt engineering, we use **Z3 Theorem Prover** (SMT Solver by Microsoft Research) to provide **deterministic, mathematically-proven** compliance verification — making AI decisions auditable, trustworthy, and legally compliant.

### 🧠 Neuro-Symbolic Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Request                       │
│         "Pay 25M VND cash for event costs"           │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  🧠 Neural Layer │  ← Gemini 1.5 Pro
              │  Semantic Parser │     (Understands language)
              └────────┬────────┘
                       │ JSON: {amount: 25M, method: cash}
              ┌────────▼────────┐
              │  ⚖️ Symbolic Layer│  ← Z3 Theorem Prover
              │  Formal Verifier │     (Mathematical proof)
              └────────┬────────┘
                       │ UNSAT ❌ (Violates tax regulation)
              ┌────────▼────────┐
              │  📋 Forensics    │  ← PostgreSQL
              │  Audit Trail     │     (Immutable log)
              └─────────────────┘
```

### 🏆 INNOSTAR 2026

This project is developed for the **INNOSTAR 2026 Student Startup Ideas Competition** — *"Applying Science & Technology in Business for the Digital Age"* — by students from the **University of Information Technology (UIT), Vietnam**.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-team/trustagent-forensics.git
cd trustagent-forensics

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

### Run Tests

```bash
pytest tests/ -v
```

### Run API Server (Phase 4+)

```bash
uvicorn src.main:app --reload
# Open: http://localhost:8000/docs
```

---

## 📁 Project Structure

```
trustagent-forensics/
├── src/
│   ├── z3_engine/          # Z3 Formal Verification Engine
│   │   ├── solver.py       # TrustAgentSolver wrapper
│   │   ├── models.py       # Pydantic data models
│   │   └── rules/          # Business rule definitions
│   ├── semantic/           # LLM Semantic Parsing (Gemini)
│   ├── agents/             # LangGraph Multi-Agent Orchestration
│   ├── api/                # FastAPI REST endpoints
│   ├── database/           # PostgreSQL Audit Trail
│   └── dashboard/          # Web Dashboard UI
├── tests/                  # Test suite
├── docs/                   # Documentation
└── docker-compose.yml      # One-command deployment
```

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Neural** | Gemini 1.5 Pro | Natural language → structured JSON |
| **Symbolic** | Z3 Theorem Prover | Mathematical compliance verification |
| **Orchestration** | LangGraph | Multi-agent workflow with self-correction |
| **Backend** | FastAPI | Async REST API server |
| **Database** | PostgreSQL (JSONB) | Immutable forensic audit trail |
| **Deployment** | Docker | Containerized deployment |

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with 🇻🇳 by <strong>UIT INNOSTAR Team</strong> for INNOSTAR 2026
</p>

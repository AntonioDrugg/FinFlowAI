# 🚀 FinFlowAI — Start Here

Welcome to **FinFlowAI**, your AI-powered personal finance assistant.

## What is FinFlowAI?

FinFlowAI helps you:
- 📊 **Track** income, expenses, and budgets
- 🤖 **Analyse** spending patterns using AI insights
- 📈 **Forecast** future cash flow from historical data
- 📝 **Generate** financial summaries and reports

---

## Project Structure

```
FinFlowAI/
├── directives/          # Step-by-step SOPs for each feature
├── execution/           # Python scripts that do the actual work
├── web/                 # Frontend (HTML/CSS/JS)
├── .tmp/                # Temp files — auto-generated, never commit
├── .env                 # Your API keys and secrets (never commit)
├── requirements.txt     # Python dependencies
└── START_HERE.md        # This file
```

---

## Setup

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure your environment
Copy `.env.example` to `.env` and fill in your keys:
```bash
copy .env.example .env
```

### 3. Run the web app (once built)
```bash
python execution/server.py
```
Then open `http://localhost:5000` in your browser.

---

## How to Work with the AI Agent

The AI agent follows the **3-layer architecture** defined in `GEMINI.md`:
- Tell the agent what you want in natural language
- It reads the relevant `directives/` SOPs
- It runs the appropriate `execution/` scripts

You never need to write code yourself unless you want to.

---

## Next Steps

1. ✅ Project scaffolded
2. ⬜ Define your first financial data source (CSV upload, bank API, manual entry)
3. ⬜ Build the transaction ingestion pipeline
4. ⬜ Set up the AI insights engine
5. ⬜ Launch the web dashboard

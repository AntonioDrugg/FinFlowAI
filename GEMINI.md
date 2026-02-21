# Agent Instructions — FinFlowAI

> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same instructions load in any AI environment.

## Project Overview

**FinFlowAI** is an AI-powered personal finance assistant. It helps users:
- Track income, expenses, and budgets
- Analyse spending patterns with AI insights
- Forecast cash flow based on historical data
- Generate financial summaries and reports

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**
- SOPs written in Markdown, live in `directives/`
- Define the goals, inputs, tools/scripts to use, outputs, and edge cases

**Layer 2: Orchestration (Decision making)**
- This is you (the AI agent). Your job: intelligent routing.
- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings

**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts in `execution/`
- API keys and secrets stored in `.env`
- Handle API calls, data processing, file operations

## File Organization

```
FinFlowAI/
├── directives/          # SOPs in Markdown (the instruction set)
├── execution/           # Python scripts (the deterministic tools)
├── web/                 # Frontend HTML/CSS/JS
├── .tmp/                # Temporary / intermediate files (never commit)
├── .env                 # Environment variables and API keys
├── .gitignore
├── requirements.txt
├── START_HERE.md        # Onboarding doc
└── GEMINI.md / CLAUDE.md / AGENTS.md
```

## Operating Principles

1. **Check for tools first** — Before writing a script, check `execution/` per the relevant directive.
2. **Self-anneal when things break** — Fix → Update script → Test → Update directive.
3. **Update directives as you learn** — Directives are living documents.
4. **Local files are intermediates** — Deliverables live in cloud or `web/`. Everything in `.tmp/` can be deleted and regenerated.

## Key Conventions

- All financial data processing goes through scripts in `execution/`
- Never hardcode API keys — always use `.env` via `python-dotenv`
- `.tmp/` is gitignored — never commit temp data
- Update `directives/` whenever you discover new constraints or better approaches

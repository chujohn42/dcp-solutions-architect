# DCP Solutions Architect

A lightweight Streamlit tool that mirrors the core workflow of a **DoorDash Commerce
Platform (DCP) Solutions Architect** — the person who helps a merchant figure out
whether DCP fits their business, what it could be worth, and how to get them live.

> Personal/portfolio project. Not affiliated with or endorsed by DoorDash.

## What it does

The app is organized as three tabs, one per stage of the SA workflow:

| Tab | Purpose |
| --- | --- |
| **1. Stack Fit** | Pick the merchant's POS/ordering setup (Toast, Olo, older POS) and loyalty program (Punchh). Get one difficulty rating (Low/Medium/High/Not scored) with a one-sentence reason, the top 2 risks and a 3-step approach. Updates instantly. |
| **2. Growth** | Enter monthly online orders, average order value and conversion rate, then switch on growth levers. See estimated extra sales per year and a bar chart of each lever's impact. Lift % can be adjusted in a collapsed panel. |
| **3. Rollout Plan** | Combines tabs 1 and 2 into a Discovery → Migration → Launch → Optimization timeline, scaled to the difficulty rating. Downloads as a detailed PDF. |

**Status:** all three tabs are built. The playbook uses the other two tabs' outputs and
exports to PDF.

Logic lives in pure-Python modules with no Streamlit code: `modules/fit_scoring.py`,
`modules/growth_model.py` and `modules/playbook.py`. Unit tests are in `tests/`; run them with `python -m pytest` (needs `requirements-dev.txt`).

## Project structure

```
dcp-solutions-architect/
├── app.py                  # Streamlit entry point: page config, sidebar, tabs
├── modules/
│   ├── fit_scoring.py          # Tab 1 scoring table, risks, phased plan (pure logic)
│   ├── tech_stack_fit.py       # Tab 1 UI
│   ├── growth_model.py         # Tab 2 SSS model, lever impact, prioritization (pure logic)
│   ├── sales_simulator.py      # Tab 2 UI
│   ├── playbook.py             # Tab 3 phase plan + timeline (pure logic)
│   ├── playbook_pdf.py         # Tab 3 PDF export (reportlab)
│   ├── onboarding_playbook.py  # Tab 3 UI
│   ├── state.py                # Shared session state, Load Example, Reset
│   ├── example_data.py         # Fictional demo merchant
│   └── styles.py               # Custom CSS + small HTML components
├── data/                   # Input files (merchant profiles, integration catalogs, etc.)
├── requirements.txt
└── README.md
```

Each module exposes a `render()` function that `app.py` calls inside its tab, so
logic stays out of the entry point.

## Demo

Click **Load example merchant** (top right) to fill in all three tabs with a fictional
fast-casual chain on Olo + Punchh. All three tabs populate at once. **Reset** clears everything.
Theme and fonts are in `.streamlit/config.toml`; extra CSS is in `modules/styles.py`.

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt   # or requirements.txt to run the app only
streamlit run app.py
```

<div align="center">

# Autonomous Art Buying Agent

### AI agents that search, evaluate, and pay — end to end. No human clicks required.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Claude](https://img.shields.io/badge/Anthropic-Claude%20Haiku-D97706?style=for-the-badge)](https://anthropic.com)
[![Tavily](https://img.shields.io/badge/Tavily-Search%20API-0EA5E9?style=for-the-badge)](https://tavily.com)
[![x402](https://img.shields.io/badge/x402-Payment%20Protocol-8B5CF6?style=for-the-badge)](https://x402.org)
[![Coinbase](https://img.shields.io/badge/Coinbase-CDP%20%2B%20Base-0052FF?style=for-the-badge&logo=coinbase)](https://coinbase.com)

**Agentic Commerce Build Day · Microsoft Garage × Tavily × Coinbase · NYTechWeek 2026**

</div>

---

## The Problem

AI agents today can search, reason, and plan. But they can't pay.

Every agentic commerce flow breaks at the checkout step — because payment requires a human to click. This project eliminates that step entirely.

---

## What It Does

Given a visual style — Van Gogh's aesthetic — the agent autonomously:

1. **Searches** the web for matching artworks in real time via Tavily
2. **Evaluates** each result using Claude Haiku with vision
3. **Purchases** matched items under $0.01 instantly via x402/USDC on Base
4. **Escalates** higher-priced matches to the designer via email with one-click approve/reject

Zero human intervention for low-value purchases. Human-in-the-loop for high-value decisions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    agent.py — run loop                       │
│              Runs every 5 min (configurable)                 │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│  search.py — Tavily API      │
│  3 Van Gogh queries          │
│  search_depth: advanced      │
│  Returns: title, url, image  │
└──────────┬───────────────────┘
           │  for each listing
           ▼
┌──────────────────────────────┐
│  evaluator.py — Claude Haiku │
│  Vision-enabled evaluation   │
│  System prompt: Van Gogh     │
│  criteria (brushstrokes,     │
│  palette, texture, subjects) │
│  Returns: match, confidence, │
│  reason (JSON, schema-safe)  │
└──────────┬───────────────────┘
           │  if match = true
           ▼
     price ≤ $0.01?
    ┌───────┴────────┐
   YES              NO
    │                │
    ▼                ▼
┌───────────┐  ┌──────────────┐
│ payment.py│  │ notifier.py  │
│ x402 flow │  │ Email        │
│           │  │ designer     │
│ POST /    │  │ with approve │
│ purchase  │  │ / reject     │
│   ↓ 402   │  │ links        │
│ pay USDC  │  └──────────────┘
│   ↓ retry │
│ X-Payment │
│ header    │
│   ↓ 200   │
│ confirmed │
└───────────┘
```

---

## The x402 Payment Protocol

x402 is a native HTTP payment protocol for AI agents. It reuses the long-forgotten HTTP `402 Payment Required` status code to create a machine-readable payment handshake:

```
Agent → POST /purchase          (buy request)
Seller ← 402                    (payment required + amount + address + network)
Agent → POST /purchase          (same request + X-Payment header with tx proof)
Seller ← 200                    (confirmed + download URL)
```

No redirects. No OAuth. No human checkout. The agent handles the entire flow programmatically.

**In production:** real USDC transfer on Base via Coinbase CDP  
**In demo mode:** simulated tx hash — same flow, no on-chain spend

---

## Code Walkthrough

### `search.py` — Real-time art discovery
```python
# 3 targeted queries, advanced depth, image URLs included
SEARCH_QUERIES = [
    "Van Gogh style art for sale original painting",
    "Van Gogh inspired artwork buy swirling brushstrokes",
    "impasto Van Gogh aesthetic print for sale",
]
```
Tavily's `search_depth: advanced` fetches full page content, not just snippets — giving Claude enough signal to evaluate aesthetic match.

### `evaluator.py` — Vision-based aesthetic scoring
```python
# Claude Haiku with vision — evaluates title + description + image
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    system=SYSTEM_PROMPT,   # Van Gogh criteria: brushstrokes, palette, texture
    messages=messages,      # includes image_url block when available
)
# Returns: {"match": true, "confidence": 0.87, "reason": "..."}
```
Schema-safe JSON output with markdown code block stripping for robustness.

### `payment.py` — x402 flow
```python
# Step 1: initial request
response = client.post(f"{SELLER_ENDPOINT}/purchase", json=payload)

# Step 2: if 402, pay and retry
if response.status_code == 402:
    payment_header = _demo_payment(payment_details)   # or _onchain_payment()
    retry = client.post(..., headers={"X-Payment": payment_header})
```
Two-path implementation: `DEMO_MODE=true` simulates tx hashes for hackathon testing; `DEMO_MODE=false` triggers real Coinbase CDP transfers on Base.

### `notifier.py` — Human-in-the-loop escalation
Above-threshold matches trigger an HTML email with embedded approve/reject links pointing back to the seller mock. The designer clicks once — no dashboard needed.

---

## Setup

```bash
git clone https://github.com/riesgopais/hackathon-buying-agent
cd hackathon-buying-agent
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python agent.py
```

The agent runs on a loop (default: every 5 minutes). Press `Ctrl+C` to stop.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TAVILY_API_KEY` | ✅ | Tavily search API key |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key (Haiku) |
| `DESIGNER_EMAIL` | ✅ | Email for approval notifications |
| `SMTP_USER` / `SMTP_PASSWORD` | ✅ | Gmail credentials |
| `SELLER_ENDPOINT` | ✅ | Seller mock base URL |
| `COINBASE_API_KEY_NAME` | Production | Coinbase CDP key name |
| `COINBASE_API_KEY_PRIVATE_KEY` | Production | Coinbase CDP private key |
| `WALLET_ID` | Production | Pre-funded USDC wallet on Base |
| `AUTO_BUY_THRESHOLD` | Optional | Max auto-purchase price (default: `0.01`) |
| `DEMO_MODE` | Optional | Simulate payments without on-chain tx (default: `true`) |
| `RUN_INTERVAL_SECONDS` | Optional | Loop interval in seconds (default: `300`) |

---

## Seller Mock — API Contract

For teams building compatible seller endpoints. The agent expects:

### `POST /purchase`

**Request:**
```json
{
  "title": "Starry Night inspired landscape",
  "url": "https://example.com/art/123",
  "price": 0.005
}
```

**Response A — Payment required (x402):**
```
HTTP 402
{ "amount": "0.01", "address": "0xYOUR_WALLET", "network": "base-sepolia" }
```
The agent retries with header:
```
X-Payment: {"tx_hash": "0xabc...", "amount": "0.01", "network": "base-sepolia", "asset": "USDC", "demo": true}
```

**Response B — Confirmed:** `HTTP 200` `{ "status": "sold", "download_url": "..." }`  
**Response C — Free item:** `HTTP 200` directly (no payment step)  
**Response D — Unavailable:** `HTTP 404` or `HTTP 410`

---

## Stack

| Layer | Technology |
|-------|-----------|
| Search | Tavily API — `search_depth: advanced`, image URLs |
| Evaluation | Claude Haiku — vision-enabled, JSON output |
| Payments | x402 protocol — HTTP 402 handshake + USDC on Base |
| On-chain | Coinbase CDP — `wallet.transfer()` |
| Notifications | SMTP email — HTML with approve/reject links |
| Runtime | Python 3.11 · `httpx` · `python-dotenv` |

---

## Key Design Decisions

**Why x402 over traditional payment APIs?** x402 is stateless, HTTP-native, and requires no OAuth or session cookies — exactly what autonomous agents need. The entire payment handshake happens in two HTTP calls.

**Why Claude Haiku with vision?** Speed and cost matter in a search loop. Haiku evaluates an image + description in ~500ms at a fraction of Sonnet's cost. For aesthetic judgment, vision access to the actual image beats text-only evaluation significantly.

**Why demo mode by default?** Hackathon testing requires fast iteration without burning real USDC. `DEMO_MODE=true` produces realistic x402 flows with the same code path — so the seller mock and agent integrate cleanly before going on-chain.

---

<div align="center">

**Built at Agentic Commerce Build Day · Microsoft Garage × Tavily × Coinbase**  
**NYTechWeek 2026 · New York City**

</div>

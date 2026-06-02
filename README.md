# Autonomous Art Buying Agent

Agentic Commerce Build Day — Microsoft Garage × Tavily × Coinbase  
NYTechWeek 2026

## What it does

Searches online art listings for Van Gogh aesthetic matches and autonomously purchases items under $0.01 via x402/USDC — or emails the designer for approval on higher-priced items.

## Flow

```
Tavily search → Claude aesthetic eval → x402 autopay (≤$0.01) or email designer (>$0.01)
```

## Setup

```bash
cp .env.example .env
# Fill in your API keys

pip install -r requirements.txt
python agent.py
```

## Environment variables

| Variable | Description |
|---|---|
| `TAVILY_API_KEY` | Tavily search API key |
| `ANTHROPIC_API_KEY` | Claude API key |
| `COINBASE_API_KEY_NAME` | Coinbase CDP key name |
| `COINBASE_API_KEY_PRIVATE_KEY` | Coinbase CDP private key |
| `WALLET_ID` | CDP wallet ID (pre-funded with USDC) |
| `DESIGNER_EMAIL` | Email to notify for manual approvals |
| `SMTP_USER` / `SMTP_PASSWORD` | Gmail credentials for notifications |
| `SELLER_ENDPOINT` | Seller mock base URL |
| `AUTO_BUY_THRESHOLD` | Max price for auto-purchase (default: 0.01) |
| `DEMO_MODE` | Set to `true` to simulate payments without real on-chain txs (default: true) |

## Stack

- **Search**: Tavily API
- **Evaluation**: Claude Haiku (vision-enabled)
- **Payments**: x402 protocol via Coinbase CDP (USDC on Base)
- **Notifications**: SMTP email with approve/reject links

---

## Seller Mock — API Contract

This section is for the team building the seller mock. The buying agent expects the following interface:

### POST `/purchase`

The agent sends a purchase request for a matched artwork.

**Request body:**
```json
{
  "title": "Starry Night inspired landscape",
  "url": "https://example.com/art/123",
  "price": 0.005
}
```

---

### Response A — Payment required (x402 flow)

If the item requires payment, respond with **HTTP 402**:

```json
{
  "amount": "0.01",
  "address": "0xYOUR_WALLET_ADDRESS",
  "network": "base-sepolia"
}
```

The agent will process the payment and retry the same request with an `X-Payment` header:

```
X-Payment: {"tx_hash": "0xabc123...", "amount": "0.01", "network": "base-sepolia", "asset": "USDC", "demo": true}
```

On retry, verify the header and respond with **HTTP 200**:

```json
{
  "status": "sold",
  "title": "Starry Night inspired landscape",
  "download_url": "https://example.com/downloads/123"
}
```

---

### Response B — Free item

If the item is free (price = 0), you can respond directly with **HTTP 200** — no payment step needed.

---

### Response C — Not available

If the item is out of stock or unavailable, respond with **HTTP 404** or **HTTP 410**.

---

### Notes

- The `demo` field in `X-Payment` will be `true` during hackathon testing — this means the tx hash is simulated, not a real on-chain transaction.
- Network is `base-sepolia` (testnet) during development.
- The agent retries exactly once after receiving a 402.

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

## Stack

- **Search**: Tavily API
- **Evaluation**: Claude Haiku (vision-enabled)
- **Payments**: x402 protocol via Coinbase CDP (USDC on Base)
- **Notifications**: SMTP email with approve/reject links

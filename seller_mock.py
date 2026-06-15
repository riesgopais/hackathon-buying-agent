"""
Seller Mock — x402 compatible endpoint for the Autonomous Art Buying Agent.

Implements the full x402 payment handshake:
  POST /purchase       → 402 (payment required) or 200 (confirmed)
  GET  /approve?url=   → approve a designer-escalated purchase
  GET  /reject?url=    → reject a designer-escalated purchase
  GET  /catalog        → browse available mock artworks
  GET  /health         → liveness check

Run:
  python3 seller_mock.py
  # or
  python3 -m uvicorn seller_mock:app --reload --port 8000
"""

import json
import hashlib
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn

app = FastAPI(title="Art Seller Mock", description="x402-compatible seller for hackathon testing")

# ── Mock art catalog ──────────────────────────────────────────────────────────
CATALOG = [
    {
        "id": "vg-001",
        "title": "Starry Night Study — Original Print",
        "artist": "Studio Van Gogh",
        "price": 0.005,
        "style": "post-impressionist",
        "download_url": "https://picsum.photos/seed/starry/800/600",
    },
    {
        "id": "vg-002",
        "title": "Sunflowers in Oil — Limited Edition",
        "artist": "Neo Impressionist Co.",
        "price": 0.008,
        "style": "post-impressionist",
        "download_url": "https://picsum.photos/seed/sunflower/800/600",
    },
    {
        "id": "vg-003",
        "title": "Wheat Field with Crows — Digital Replica",
        "artist": "Atelier Moderne",
        "price": 0.50,  # above threshold → triggers designer approval
        "style": "post-impressionist",
        "download_url": "https://picsum.photos/seed/wheat/800/600",
    },
    {
        "id": "vg-004",
        "title": "Irises Study — Free Community Edition",
        "artist": "Open Canvas",
        "price": 0.0,   # free → no payment step
        "style": "post-impressionist",
        "download_url": "https://picsum.photos/seed/irises/800/600",
    },
    {
        "id": "vg-005",
        "title": "Bedroom in Arles — High-res Scan",
        "artist": "Archive Project",
        "price": 0.01,
        "style": "post-impressionist",
        "download_url": "https://picsum.photos/seed/bedroom/800/600",
    },
]

# In-memory store: url → "pending" | "approved" | "rejected"
designer_queue: dict[str, str] = {}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _item_by_url(url: str):
    for item in CATALOG:
        if item["id"] in url or item["title"].lower() in url.lower():
            return item
    return None

def _download_url(title: str) -> str:
    seed = hashlib.md5(title.encode()).hexdigest()[:8]
    return f"https://picsum.photos/seed/{seed}/800/600"

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "catalog_size": len(CATALOG)}


@app.get("/catalog")
def catalog():
    return {"items": CATALOG}


@app.post("/purchase")
async def purchase(request: Request):
    body = await request.json()
    title  = body.get("title", "Unknown")
    url    = body.get("url", "")
    price  = float(body.get("price", 0.0))

    x_payment = request.headers.get("X-Payment")

    print(f"\n[seller] POST /purchase — '{title}' @ ${price}")

    # ── Payment already attached (retry after 402) ────────────────────────────
    if x_payment:
        try:
            payment = json.loads(x_payment)
            tx = payment.get("tx_hash", "demo")
            demo = payment.get("demo", False)
            print(f"[seller] Payment received — tx: {tx[:16]}... demo={demo}")
            return {
                "status": "sold",
                "title": title,
                "download_url": _download_url(title),
                "tx_hash": tx,
                "demo": demo,
            }
        except Exception as e:
            print(f"[seller] Bad X-Payment header: {e}")
            return JSONResponse(status_code=400, content={"error": "Invalid X-Payment header"})

    # ── Free item — no payment needed ─────────────────────────────────────────
    if price == 0:
        print("[seller] Free item — returning 200 directly")
        return {
            "status": "sold",
            "title": title,
            "download_url": _download_url(title),
            "tx_hash": None,
        }

    # ── Paid item — return 402 ────────────────────────────────────────────────
    print(f"[seller] Returning 402 — requires ${price} USDC on base-sepolia")
    return JSONResponse(
        status_code=402,
        content={
            "amount": str(price),
            "address": "0xDeAdBeEf00000000000000000000000000000001",  # demo wallet
            "network": "base-sepolia",
        },
    )


@app.get("/approve")
def approve(url: str = Query(...)):
    designer_queue[url] = "approved"
    print(f"[seller] APPROVED — {url}")
    return HTMLResponse(content=f"""
    <html><body style="font-family:sans-serif;padding:40px;background:#f0fdf4">
    <h2 style="color:#16a34a">✅ Purchase approved</h2>
    <p>The agent will process this purchase on its next run.</p>
    <p style="color:#888;font-size:12px">{url}</p>
    </body></html>
    """)


@app.get("/reject")
def reject(url: str = Query(...)):
    designer_queue[url] = "rejected"
    print(f"[seller] REJECTED — {url}")
    return HTMLResponse(content=f"""
    <html><body style="font-family:sans-serif;padding:40px;background:#fef2f2">
    <h2 style="color:#dc2626">❌ Purchase rejected</h2>
    <p>The item has been discarded from the queue.</p>
    <p style="color:#888;font-size:12px">{url}</p>
    </body></html>
    """)


@app.get("/queue")
def queue():
    """Inspect designer approval queue (debug endpoint)."""
    return {"queue": designer_queue}


# ── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting Art Seller Mock on http://localhost:8000")
    print("Catalog: /catalog | Health: /health | Queue: /queue\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)

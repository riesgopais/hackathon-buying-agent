import httpx
import os
import json
import uuid
import time

SELLER_ENDPOINT = os.environ.get("SELLER_ENDPOINT", "http://localhost:8000")
DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() == "true"

def attempt_purchase(listing: dict) -> dict:
    """
    Execute x402 payment flow against seller mock endpoint.

    Flow:
    1. POST /purchase with listing details
    2. If 402 → generate payment proof (demo) or pay on-chain (prod) → retry with X-Payment header
    3. If 200 → return success
    """
    payload = {
        "title": listing["title"],
        "url": listing["url"],
        "price": listing.get("price", 0.01),
    }

    with httpx.Client() as client:
        response = client.post(f"{SELLER_ENDPOINT}/purchase", json=payload)

        if response.status_code == 200:
            return {"status": "purchased", "data": response.json()}

        if response.status_code == 402:
            payment_details = response.json()
            print(f"   [x402] Payment required: {payment_details}")

            payment_header = _demo_payment(payment_details) if DEMO_MODE else _onchain_payment(payment_details)

            if not payment_header:
                return {"status": "payment_failed", "reason": "Could not execute payment"}

            retry = client.post(
                f"{SELLER_ENDPOINT}/purchase",
                json=payload,
                headers={"X-Payment": payment_header},
            )

            if retry.status_code == 200:
                return {"status": "purchased", "data": retry.json()}
            return {"status": "failed", "reason": retry.text}

    return {"status": "failed", "reason": "Unexpected response"}


def _demo_payment(payment_details: dict) -> str:
    """Simulate x402 payment for demo — generates a fake but realistic tx proof."""
    amount = payment_details.get("amount", "0.01")
    network = payment_details.get("network", "base-sepolia")
    fake_tx = f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:24]}"

    print(f"   [x402 DEMO] Simulating USDC transfer on {network}")
    print(f"   [x402 DEMO] Amount: {amount} USDC")
    print(f"   [x402 DEMO] TX: {fake_tx}")
    time.sleep(0.5)  # simulate block confirmation

    return json.dumps({
        "tx_hash": fake_tx,
        "amount": amount,
        "network": network,
        "asset": "USDC",
        "demo": True,
    })


def _onchain_payment(payment_details: dict) -> str | None:
    """Send real USDC payment via Coinbase CDP (production)."""
    try:
        from cdp import Cdp, Wallet

        Cdp.configure(
            api_key_name=os.environ["COINBASE_API_KEY_NAME"],
            api_key_private_key=os.environ["COINBASE_API_KEY_PRIVATE_KEY"],
        )

        wallet = Wallet.fetch(os.environ["WALLET_ID"])
        amount = payment_details.get("amount", "0.01")
        to_address = payment_details.get("address")
        network = payment_details.get("network", "base-mainnet")

        transfer = wallet.transfer(
            amount=amount,
            asset_id="usdc",
            destination=to_address,
            network_id=network,
        ).wait()

        return json.dumps({
            "tx_hash": transfer.transaction_hash,
            "amount": amount,
            "network": network,
            "asset": "USDC",
        })

    except Exception as e:
        print(f"   [payment] Error: {e}")
        return None

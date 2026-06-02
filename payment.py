import httpx
import os
import json

SELLER_ENDPOINT = os.environ.get("SELLER_ENDPOINT", "http://localhost:8000")

def attempt_purchase(listing: dict) -> dict:
    """
    Execute x402 payment flow against seller mock endpoint.

    Flow:
    1. POST /purchase with listing details
    2. If 402 → parse payment requirements → pay via Coinbase CDP → retry with X-Payment header
    3. If 200 → return success
    """
    payload = {
        "title": listing["title"],
        "url": listing["url"],
        "price": listing.get("price", 0.01),
    }

    with httpx.Client() as client:
        # Initial purchase request
        response = client.post(f"{SELLER_ENDPOINT}/purchase", json=payload)

        if response.status_code == 200:
            return {"status": "purchased", "data": response.json()}

        if response.status_code == 402:
            payment_details = response.json()
            payment_header = _execute_payment(payment_details)

            if not payment_header:
                return {"status": "payment_failed", "reason": "Could not execute on-chain payment"}

            # Retry with payment proof
            retry = client.post(
                f"{SELLER_ENDPOINT}/purchase",
                json=payload,
                headers={"X-Payment": payment_header},
            )

            if retry.status_code == 200:
                return {"status": "purchased", "data": retry.json()}
            return {"status": "failed", "reason": retry.text}

    return {"status": "failed", "reason": "Unexpected response"}


def _execute_payment(payment_details: dict) -> str | None:
    """
    Send USDC payment via Coinbase CDP and return payment proof header.
    Requires COINBASE_API_KEY_NAME and COINBASE_API_KEY_PRIVATE_KEY env vars.
    """
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
        })

    except Exception as e:
        print(f"[payment] CDP error: {e}")
        return None

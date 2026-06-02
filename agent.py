"""
Autonomous Art Buying Agent
Agentic Commerce Build Day — Microsoft Garage x Tavily x Coinbase
"""

import os
import time
from dotenv import load_dotenv
load_dotenv()

from search import search_art_listings
from evaluator import evaluate_aesthetic
from payment import attempt_purchase
from notifier import notify_designer, notify_purchase_confirmed

THRESHOLD = float(os.environ.get("AUTO_BUY_THRESHOLD", 0.01))
RUN_INTERVAL = int(os.environ.get("RUN_INTERVAL_SECONDS", 300))  # default: every 5 min


def run_once():
    print("\n" + "=" * 50)
    print(f"[agent] Starting run — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    listings = search_art_listings()
    print(f"[search] Found {len(listings)} listings\n")

    purchased, flagged, discarded = [], [], []

    for listing in listings:
        title = listing["title"]
        print(f"[eval] {title}")

        evaluation = evaluate_aesthetic(
            title=title,
            description=listing.get("description", ""),
            image_url=listing.get("image_url", ""),
        )

        if not evaluation.get("match"):
            print(f"  ✗ No match — {evaluation.get('reason', '')}\n")
            discarded.append(listing)
            continue

        confidence = evaluation.get("confidence", 0)
        price = listing.get("price", 0)
        print(f"  ✓ Match — confidence {confidence:.0%} — price ${price}")

        if price <= THRESHOLD:
            print(f"  💳 Auto-purchasing via x402...")
            result = attempt_purchase(listing)
            if result["status"] == "purchased":
                print(f"  ✅ Purchased — sending confirmation email\n")
                purchased.append({**listing, "result": result})
                notify_purchase_confirmed(listing, evaluation, result)
            else:
                print(f"  ❌ Purchase failed: {result.get('reason')}\n")
        else:
            print(f"  📧 Above threshold — notifying designer for approval\n")
            notify_designer(listing, evaluation)
            flagged.append(listing)

    print("─" * 50)
    print(f"  Purchased : {len(purchased)}")
    print(f"  Flagged   : {len(flagged)}")
    print(f"  Discarded : {len(discarded)}")
    print("─" * 50)


def run_loop():
    print(f"[agent] Running every {RUN_INTERVAL}s. Press Ctrl+C to stop.\n")
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[agent] Error during run: {e}")
        print(f"[agent] Next run in {RUN_INTERVAL}s...")
        time.sleep(RUN_INTERVAL)


if __name__ == "__main__":
    run_loop()

"""
Autonomous Art Buying Agent
Agentic Commerce Build Day — Microsoft Garage x Tavily x Coinbase
"""

import os
from dotenv import load_dotenv
load_dotenv()

from search import search_art_listings
from evaluator import evaluate_aesthetic
from payment import attempt_purchase
from notifier import notify_designer

THRESHOLD = float(os.environ.get("AUTO_BUY_THRESHOLD", 0.01))

def run():
    print("🔍 Searching for Van Gogh style art...")
    listings = search_art_listings()
    print(f"   Found {len(listings)} listings\n")

    purchased = []
    flagged = []
    discarded = []

    for listing in listings:
        title = listing["title"]
        print(f"🎨 Evaluating: {title}")

        evaluation = evaluate_aesthetic(
            title=title,
            description=listing.get("description", ""),
            image_url=listing.get("image_url", ""),
        )

        if not evaluation.get("match"):
            print(f"   ✗ No match ({evaluation.get('reason', '')})\n")
            discarded.append(listing)
            continue

        confidence = evaluation.get("confidence", 0)
        price = listing.get("price", 0)
        print(f"   ✓ Match! Confidence: {confidence:.0%} — Price: ${price}")

        if price <= THRESHOLD:
            print(f"   💳 Auto-purchasing via x402...")
            result = attempt_purchase(listing)
            if result["status"] == "purchased":
                print(f"   ✅ Purchased!\n")
                purchased.append({**listing, "result": result})
            else:
                print(f"   ❌ Purchase failed: {result.get('reason')}\n")
        else:
            print(f"   📧 Price above threshold — notifying designer...\n")
            notify_designer(listing, evaluation)
            flagged.append(listing)

    print("─" * 50)
    print(f"✅ Purchased:  {len(purchased)}")
    print(f"📧 Flagged:    {len(flagged)}")
    print(f"✗  Discarded:  {len(discarded)}")

if __name__ == "__main__":
    run()

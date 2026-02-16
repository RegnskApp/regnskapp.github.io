import os
import json
import time
import requests
import jwt
from collections import defaultdict

# ========= KONFIG =========

APP_ID = "6743946348"
HISTORY_FILE = "data/asc_history.json"

ASC_ISSUER_ID = os.environ["ASC_ISSUER_ID"]
ASC_KEY_ID = os.environ["ASC_KEY_ID"]
ASC_PRIVATE_KEY = os.environ["ASC_PRIVATE_KEY"].replace("\\n", "\n")

# Bootstrap-verdier (første gang scriptet kjøres)
BOOTSTRAP_TOTAL_RATINGS = 10
BOOTSTRAP_STARS = {
    "5": 8,
    "4": 2,
    "3": 0,
    "2": 0,
    "1": 0,
}


# ========= JWT TOKEN =========

def create_token():
    now = int(time.time())

    payload = {
        "iss": ASC_ISSUER_ID,
        "iat": now,
        "exp": now + 1200,
        "aud": "appstoreconnect-v1",
    }

    headers = {
        "alg": "ES256",
        "kid": ASC_KEY_ID,
        "typ": "JWT",
    }

    return jwt.encode(payload, ASC_PRIVATE_KEY, algorithm="ES256", headers=headers)


# ========= HENT REVIEWS =========

def fetch_all_reviews(token):
    url = f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/customerReviews"
    headers = {"Authorization": f"Bearer {token}"}

    reviews = []

    while url:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

        reviews.extend(data.get("data", []))
        url = data.get("links", {}).get("next")

    return reviews


# ========= LAST HISTORIKK =========

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {
            "ratings": {
                "total_count": BOOTSTRAP_TOTAL_RATINGS,
                "average": round(
                    sum(int(star) * count for star, count in BOOTSTRAP_STARS.items())
                    / BOOTSTRAP_TOTAL_RATINGS,
                    2,
                ),
                "stars": BOOTSTRAP_STARS.copy(),
                "review_ids": [],
            }
        }

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ========= LAGRE HISTORIKK =========

def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ========= OPPDATER RATINGS =========

def update_ratings(history, reviews):
    ratings = history["ratings"]

    existing_ids = set(ratings.get("review_ids", []))
    new_reviews = [r for r in reviews if r["id"] not in existing_ids]

    if not new_reviews:
        print("Ingen nye reviews.")
        return history

    # Tell nye stjerner
    star_counter = defaultdict(int)

    for r in new_reviews:
        rating = str(r["attributes"]["rating"])
        star_counter[rating] += 1

    # Oppdater totals
    for star, count in star_counter.items():
        ratings["stars"][star] += count
        ratings["total_count"] += count

    # Legg til review-IDer
    ratings["review_ids"].extend(r["id"] for r in new_reviews)

    # Regn nytt snitt
    total_score = sum(int(star) * count for star, count in ratings["stars"].items())
    ratings["average"] = round(total_score / ratings["total_count"], 2)

    print(f"Nye reviews funnet: {len(new_reviews)}")
    return history


# ========= MAIN =========

def main():
    token = create_token()
    reviews = fetch_all_reviews(token)

    history = load_history()
    history = update_ratings(history, reviews)

    save_history(history)
    print("Ratings oppdatert og lagret.")


if __name__ == "__main__":
    main()

import os
import json
import time
import requests
from collections import defaultdict
import jwt

# ========= KONFIG =========
APP_ID = "6743946348"
HISTORY_FILE = "data/asc_reviews.json"

ASC_ISSUER_ID = os.environ["ASC_ISSUER_ID"]
ASC_KEY_ID = os.environ["ASC_KEY_ID"]
ASC_PRIVATE_KEY = os.environ["ASC_PRIVATE_KEY"].replace("\\n", "\n")

# ========= JWT TOKEN =========
def create_token():
    now = int(time.time())
    payload = {
        "iss": ASC_ISSUER_ID,
        "iat": now,
        "exp": now + 1200,
        "aud": "appstoreconnect-v1",
    }
    headers = {"alg": "ES256", "kid": ASC_KEY_ID, "typ": "JWT"}
    return jwt.encode(payload, ASC_PRIVATE_KEY, algorithm="ES256", headers=headers)

# ========= HENT ALLE REVIEWS =========
def fetch_all_reviews(token):
    url = f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/customerReviews"
    headers = {"Authorization": f"Bearer {token}"}
    reviews = []

    while url:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        reviews.extend(data.get("data", []))
        url = data.get("links", {}).get("next")  # pagination

    return reviews

# ========= LAST HISTORIKK =========
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"ratings": {}, "reviews": [], "review_ids": []}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ========= LAGRE HISTORIKK =========
def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

# ========= OPPDATER HISTORY =========
def update_history(history, reviews):
    existing_ids = set(history.get("review_ids", []))
    new_reviews = []

    # Bare nye reviews
    for r in reviews:
        review_id = r["id"]
        if review_id not in existing_ids:
            attributes = r.get("attributes", {})
            review_entry = {
                "id": review_id,
                "rating": attributes.get("rating"),
                "title": attributes.get("title", ""),
                "review": attributes.get("review", ""),
                "reviewerNickname": attributes.get("reviewerNickname", ""),
                "createdDate": attributes.get("createdDate", ""),
                "territory": attributes.get("territory", "")
            }
            new_reviews.append(review_entry)

    if new_reviews:
        print(f"Nye reviews: {len(new_reviews)}")
        history.setdefault("reviews", []).extend(new_reviews)
        history.setdefault("review_ids", []).extend(r["id"] for r in new_reviews)
    else:
        print("Ingen nye reviews.")

    # Lag summary
    star_counts = defaultdict(int)
    total_score = 0
    total_count = 0

    for r in history.get("reviews", []):
        rating = r.get("rating")
        if rating is not None:
            star_counts[str(rating)] += 1
            total_score += rating
            total_count += 1

    average = round(total_score / total_count, 2) if total_count else 0
    # Sørg for alle stjerner vises
    stars = {str(i): star_counts.get(str(i), 0) for i in range(1, 6)}

    history["ratings"] = {
        "total_count": total_count,
        "average": average,
        "stars": stars
    }

    return history

# ========= MAIN =========
def main():
    token = create_token()
    reviews = fetch_all_reviews(token)

    history = load_history()
    history = update_history(history, reviews)
    save_history(history)

    print(f"Ratings oppdatert. Totalt: {history['ratings']['total_count']} ratings, snitt: {history['ratings']['average']}")

if __name__ == "__main__":
    main()

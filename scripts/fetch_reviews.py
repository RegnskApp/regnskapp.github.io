import os
import json
import time
import requests
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

# ========= HENT REVIEWS =========

def fetch_reviews(token):
    """Hent alle reviews med tekst"""
    url = f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/customerReviews"
    headers = {"Authorization": f"Bearer {token}"}
    reviews = []

    while url:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        for rdata in data.get("data", []):
            attributes = rdata.get("attributes", {})
            reviews.append({
                "id": rdata["id"],
                "reviewerNickname": attributes.get("reviewerNickname"),
                "createdDate": attributes.get("createdDate"),
                "territory": attributes.get("territory"),
                "review": attributes.get("review")  # kan være None
            })
        url = data.get("links", {}).get("next")

    return reviews

# ========= HENT RATING SUMMARY =========

def fetch_rating_summary(token):
    """Hent korrekt total_count, stjerner og snitt (inkl. reviews uten tekst)"""
    url = f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/customerReviews/summary"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()

    summary = data.get("data", {}).get("attributes", {})
    stars = {
        "5": summary.get("fiveStarCount", 0),
        "4": summary.get("fourStarCount", 0),
        "3": summary.get("threeStarCount", 0),
        "2": summary.get("twoStarCount", 0),
        "1": summary.get("oneStarCount", 0),
    }
    total_count = summary.get("ratingCount", 0)
    average = summary.get("averageRating", 0)

    return {
        "total_count": total_count,
        "average": average,
        "stars": stars
    }

# ========= LAST HISTORIKK =========

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"ratings": {}, "review_ids": [], "reviews": []}

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ========= LAGRE HISTORIKK =========

def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

# ========= OPPDATER HISTORY =========

def update_history(history, rating_summary, reviews):
    """Oppdater ratings med summary og legg til nye reviews"""
    history["ratings"] = rating_summary

    existing_ids = set(history.get("review_ids", []))
    new_reviews = [r for r in reviews if r["id"] not in existing_ids]

    if new_reviews:
        print(f"Nye reviews funnet: {len(new_reviews)}")
        history.setdefault("review_ids", []).extend(r["id"] for r in new_reviews)
        history.setdefault("reviews", []).extend(new_reviews)
    else:
        print("Ingen nye reviews.")

    return history

# ========= MAIN =========

def main():
    token = create_token()
    rating_summary = fetch_rating_summary(token)
    reviews = fetch_reviews(token)

    history = load_history()
    history = update_history(history, rating_summary, reviews)
    save_history(history)

    print(f"Ratings oppdatert. Totalt: {history['ratings']['total_count']} ratings, snitt: {history['ratings']['average']}")

if __name__ == "__main__":
    main()

import os
import json
import time
import requests
import jwt
from collections import defaultdict

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
def fetch_reviews(token):
    """Hent alle reviews med tekst"""
    url = f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/customerReviews?limit=200"
    headers = {"Authorization": f"Bearer {token}"}
    reviews = []

    while url:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        for item in data.get("data", []):
            attr = item.get("attributes", {})
            reviews.append({
                "id": item.get("id"),
                "rating": attr.get("rating"),
                "title": attr.get("title", ""),
                "review": attr.get("body", ""),
                "reviewerNickname": attr.get("reviewerNickname", ""),
                "createdDate": attr.get("createdDate", ""),
                "territory": attr.get("territory", "")
            })
        url = data.get("links", {}).get("next")

    return reviews

# ========= GENERER RATING SUMMARY =========
def summarize_ratings(reviews):
    stars = {"5":0,"4":0,"3":0,"2":0,"1":0}
    total = 0
    sum_rating = 0
    country_data = defaultdict(list)

    for r in reviews:
        rating = r.get("rating")
        territory = r.get("territory", "UNKNOWN")
        if rating:
            rating_str = str(rating)
            if rating_str in stars:
                stars[rating_str] += 1
            sum_rating += rating
            total += 1
            country_data[territory].append(rating)

    average = round(sum_rating / total, 2) if total > 0 else 0

    # Gjennomsnitt per land
    ratings_per_country = {}
    for country, ratings in country_data.items():
        count = len(ratings)
        avg = round(sum(ratings) / count, 2) if count > 0 else 0
        ratings_per_country[country] = {"total_count": count, "average": avg}

    return {"total_count": total, "average": average, "stars": stars, "ratings_per_country": ratings_per_country}

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
    """Legg til nye reviews uten duplikater og oppdater rating summary"""
    existing_ids = set(history.get("review_ids", []))
    new_reviews = [r for r in reviews if r["id"] not in existing_ids]

    if new_reviews:
        print(f"Nye reviews lagt til: {len(new_reviews)}")
        history.setdefault("reviews", []).extend(new_reviews)
        history.setdefault("review_ids", []).extend(r["id"] for r in new_reviews)
    else:
        print("Ingen nye reviews.")

    # Oppdater rating summary
    history["ratings"] = summarize_ratings(history["reviews"])

    return history

# ========= MAIN =========
def main():
    token = create_token()
    reviews = fetch_reviews(token)
    history = load_history()
    history = update_history(history, reviews)
    save_history(history)

    print(f"Totalt reviews lagret: {len(history['reviews'])}")
    print("Rating summary:")
    print(json.dumps(history["ratings"], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

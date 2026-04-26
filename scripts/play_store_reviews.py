import os
import json
import pandas as pd
from datetime import datetime, timezone
from google.cloud import storage
from io import StringIO

# =========================
# KONFIG
# =========================
BUCKET_NAME = "pubsite_prod_4639390102037107647"
PREFIX = "reviews/"
PACKAGE_NAME = "com.balancetrackr.app"
OUTPUT_FILE = "data/play_store_reviews.json"

# =========================
# LAST UPDATED
# =========================
last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# =========================
# INIT STORAGE
# =========================
credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

if not credentials_path:
    raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS mangler")

client = storage.Client.from_service_account_json(credentials_path)
bucket = client.bucket(BUCKET_NAME)

# =========================
# HENT ALLE REVIEW-FILER
# =========================
blobs = list(bucket.list_blobs(prefix=PREFIX))

review_files = [
    b for b in blobs
    if b.name.lower().endswith(".csv") or ".csv" in b.name.lower()
]

print(f"Fant {len(review_files)} review-filer")

reviews = []

# =========================
# LES ALLE CSV-FILER
# =========================
for blob in review_files:
    print("Leser:", blob.name)

    content = blob.download_as_text()
    df = pd.read_csv(StringIO(content))

    # Rens kolonnenavn
    df.columns = [c.strip() for c in df.columns]

    # Kun din app
    if "Package Name" in df.columns:
        df = df[df["Package Name"] == PACKAGE_NAME]

    # Dato filen sist ble oppdatert i Google Cloud Storage
    file_updated = blob.updated.strftime("%Y-%m-%d") if blob.updated else ""

    for _, row in df.iterrows():
        # Rating
        try:
            rating = int(row.get("Star Rating"))
        except Exception:
            continue

        # Review dato
        submit_datetime = row.get("Review Submit Date and Time", "")
        review_date = ""

        if pd.notna(submit_datetime) and str(submit_datetime).strip():
            try:
                review_date = pd.to_datetime(submit_datetime).strftime("%Y-%m-%d")
            except Exception:
                review_date = str(submit_datetime).strip()

        review = {
            "date": review_date,
            "rating": rating,
            "title": "" if pd.isna(row.get("Review Title", "")) else str(row.get("Review Title", "")).strip(),
            "text": "" if pd.isna(row.get("Review Text", "")) else str(row.get("Review Text", "")).strip(),
            "link": "" if pd.isna(row.get("Review Link", "")) else str(row.get("Review Link", "")).strip(),
            "file_updated": file_updated
        }

        reviews.append(review)

# =========================
# SORTER REVIEWS
# =========================
reviews = sorted(
    reviews,
    key=lambda x: x.get("date", "")
)

# =========================
# OPPSUMMERINGER
# =========================
total_reviews = len(reviews)

by_rating = {
    "5": 0,
    "4": 0,
    "3": 0,
    "2": 0,
    "1": 0
}

for review in reviews:
    rating_key = str(review["rating"])

    if rating_key in by_rating:
        by_rating[rating_key] += 1

if total_reviews > 0:
    average_rating = round(
        sum(r["rating"] for r in reviews) / total_reviews,
        2
    )
else:
    average_rating = 0

# =========================
# OUTPUT
# =========================
result = {
    "last_updated": last_updated,
    "total_reviews": total_reviews,
    "average_rating": average_rating,
    "by_rating": by_rating,
    "reviews": reviews
}

os.makedirs("data", exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# =========================
# LOGGING
# =========================
print("\n✅ FERDIG")
print("🕒 Last updated:", last_updated)
print("📝 Total reviews:", total_reviews)
print("⭐ Average rating:", average_rating)
print("⭐ 5 stars:", by_rating["5"])
print("⭐ 4 stars:", by_rating["4"])
print("⭐ 3 stars:", by_rating["3"])
print("⭐ 2 stars:", by_rating["2"])
print("⭐ 1 star:", by_rating["1"])
print("📄 Output:", OUTPUT_FILE)

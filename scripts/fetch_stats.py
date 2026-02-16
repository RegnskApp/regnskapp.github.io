import os
import time
import json
import jwt
import requests
import datetime
import gzip

# =========================
# ENVIRONMENT VARIABLES
# =========================
ISSUER_ID = os.environ["ASC_ISSUER_ID"]
KEY_ID = os.environ["ASC_KEY_ID"]
PRIVATE_KEY = os.environ["ASC_PRIVATE_KEY"].replace("\\n", "\n")
VENDOR_NUMBER = os.environ["ASC_VENDOR_NUMBER"]

# =========================
# CREATE JWT TOKEN
# =========================
def create_token():
    return jwt.encode(
        {
            "iss": ISSUER_ID,
            "exp": int(time.time()) + 1200,
            "aud": "appstoreconnect-v1",
        },
        PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": KEY_ID},
    )


headers = {
    "Authorization": f"Bearer {create_token()}",
}

# =========================
# DATE (YESTERDAY)
# =========================
yesterday = (
    datetime.date.today() - datetime.timedelta(days=1)
).strftime("%Y-%m-%d")

# =========================
# FETCH SALES & TRENDS REPORT
# =========================
sales_response = requests.get(
    "https://api.appstoreconnect.apple.com/v1/salesReports",
    headers=headers,
    params={
        "filter[reportDate]": yesterday,
        "filter[reportType]": "SALES",
        "filter[frequency]": "DAILY",
        "filter[reportSubType]": "SUMMARY",
        "filter[vendorNumber]": VENDOR_NUMBER,
    },
)

# ---- Validate response ----
if sales_response.status_code != 200:
    raise Exception(
        f"Sales API HTTP error {sales_response.status_code}:\n{sales_response.text}"
    )

content_type = sales_response.headers.get("Content-Type", "")

if "gzip" in content_type:
    sales_report_text = gzip.decompress(sales_response.content).decode("utf-8")
else:
    # Apple returned JSON error instead of gzip report
    raise Exception(
        f"Sales API returned non-gzip response:\n{sales_response.text}"
    )

# =========================
# FETCH REVIEWS
# =========================
reviews_response = requests.get(
    "https://api.appstoreconnect.apple.com/v1/customerReviews",
    headers=headers,
    params={"limit": 200},
)

if reviews_response.status_code != 200:
    raise Exception(
        f"Reviews API HTTP error {reviews_response.status_code}:\n{reviews_response.text}"
    )

reviews_json = reviews_response.json()
reviews_list = reviews_json.get("data", [])

# =========================
# BUILD OUTPUT STRUCTURE
# =========================
output = {
    "generated_at_unix": int(time.time()),
    "report_date": yesterday,
    "sales_report_raw": sales_report_text,  # inneholder land + device + downloads
    "reviews": {
        "count": len(reviews_list),
        "latest": reviews_list[:50],  # begrens størrelse
    },
}

# =========================
# WRITE JSON FILE
# =========================
os.makedirs("data", exist_ok=True)

with open("data/asc_daily.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("ASC daily stats written to data/asc_daily.json")

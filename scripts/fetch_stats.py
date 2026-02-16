import os, time, json, jwt, requests, datetime, gzip, io

ISSUER_ID = os.environ["ASC_ISSUER_ID"]
KEY_ID = os.environ["ASC_KEY_ID"]
PRIVATE_KEY = os.environ["ASC_PRIVATE_KEY"].replace("\\n", "\n")

def token():
    return jwt.encode(
        {"iss": ISSUER_ID, "exp": int(time.time()) + 1200, "aud": "appstoreconnect-v1"},
        PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": KEY_ID},
    )

headers = {"Authorization": f"Bearer {token()}"}

# ---------------- SALES & TRENDS ----------------
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

sales_res = requests.get(
    "https://api.appstoreconnect.apple.com/v1/salesReports",
    headers=headers,
    params={
        "filter[reportDate]": yesterday,
        "filter[reportType]": "SALES",
        "filter[frequency]": "DAILY",
        "filter[reportSubType]": "SUMMARY",
        "filter[vendorNumber]": "YOUR_VENDOR_NUMBER"
    },
)

sales_data = gzip.decompress(sales_res.content).decode("utf-8")

# ---------------- REVIEWS ----------------
reviews_res = requests.get(
    "https://api.appstoreconnect.apple.com/v1/customerReviews",
    headers=headers,
)
reviews = reviews_res.json().get("data", [])

# ---------------- OUTPUT ----------------
output = {
    "date": yesterday,
    "sales_raw_report": sales_data,
    "reviews_count": len(reviews),
    "reviews": reviews[:50],  # begrens for størrelse
}

os.makedirs("data", exist_ok=True)

with open("data/asc_daily.json", "w") as f:
    json.dump(output, f, indent=2)

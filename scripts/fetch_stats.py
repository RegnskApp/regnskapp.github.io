import os
import time
import json
import jwt
import requests
import datetime
import gzip
import csv
from io import StringIO

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

headers = {"Authorization": f"Bearer {create_token()}"}

# =========================
# DATE (YESTERDAY)
# =========================
yesterday = (
    datetime.date.today() - datetime.timedelta(days=1)
).strftime("%Y-%m-%d")

# =========================
# FETCH SALES REPORT
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

if sales_response.status_code != 200:
    raise Exception(
        f"Sales API HTTP error {sales_response.status_code}:\n{sales_response.text}"
    )

content_type = sales_response.headers.get("Content-Type", "")
if "gzip" in content_type:
    sales_report_text = gzip.decompress(sales_response.content).decode("utf-8")
else:
    raise Exception(
        f"Sales API returned non-gzip response:\n{sales_response.text}"
    )

# =========================
# FIND APP ID
# =========================
apps_response = requests.get(
    "https://api.appstoreconnect.apple.com/v1/apps",
    headers=headers,
    params={"limit": 1},
)

if apps_response.status_code != 200:
    raise Exception(
        f"Apps API HTTP error {apps_response.status_code}:\n{apps_response.text}"
    )

apps_json = apps_response.json()
app_id = apps_json["data"][0]["id"]
app_name = apps_json["data"][0]["attributes"]["name"]

# =========================
# FETCH REVIEWS FOR APP
# =========================
reviews_response = requests.get(
    f"https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews",
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
# PARSE SALES TSV
# =========================
sales_data = []
total_units = 0

tsv_io = StringIO(sales_report_text)
reader = csv.DictReader(tsv_io, delimiter="\t")
for row in reader:
    units = int(row.get("Units", 0))
    total_units += units
    sales_data.append({
        "provider": row.get("Provider"),
        "country": row.get("Provider Country"),
        "country_code": row.get("Country Code"),
        "sku": row.get("SKU"),
        "version": row.get("Version"),
        "product_type": row.get("Product Type Identifier"),
        "units": units,
        "device": row.get("Device"),
        "platform": row.get("Supported Platforms"),
    })

# Statistik per land
sales_by_country = {}
for entry in sales_data:
    country = entry["country_code"]
    sales_by_country[country] = sales_by_country.get(country, 0) + entry["units"]

# Statistik per enhet
sales_by_device = {}
for entry in sales_data:
    device = entry["device"]
    sales_by_device[device] = sales_by_device.get(device, 0) + entry["units"]

# =========================
# BUILD OUTPUT JSON
# =========================
output = {
    "generated_at_unix": int(time.time()),
    "report_date": yesterday,
    "app": {
        "id": app_id,
        "name": app_name,
    },
    "total_units": total_units,
    "sales_by_country": sales_by_country,
    "sales_by_device": sales_by_device,
    "sales_raw": sales_data,  # alle linjer med detalj info
    "reviews": {
        "count": len(reviews_list),
        "latest": reviews_list[:50],
    },
}

# =========================
# WRITE FILE
# =========================
os.makedirs("data", exist_ok=True)
with open("data/asc_daily.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("ASC daily stats written to data/asc_daily.json")

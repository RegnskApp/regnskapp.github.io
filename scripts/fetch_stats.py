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
# BASELINE (TOTALS UP TO "YESTERDAY" BEFORE THIS HISTORY RESTART)
# =========================
BASELINE_TOTAL_UNITS_ALL_TIME = 867

BASELINE_TOTAL_PER_COUNTRY = {
    "United States": 307,
    "Norway": 96,
    "China mainland": 49,
    "Canada": 28,
    "India": 26,
    "United Kingdom": 26,
    "Germany": 24,
    "Italy": 23,
    "Australia": 16,
    "France": 16,
    "Japan": 16,
    "Taiwan": 15,
    "Spain": 14,
    "Netherlands": 13,
    "Singapore": 11,
    "Hong Kong": 10,
    "Malaysia": 8,
    "Mexico": 8,
    "Saudi Arabia": 8,
    "Ukraine": 8,
    "Greece": 7,
    "Philippines": 7,
    "Sweden": 7,
    "Türkiye": 7,
    "Austria": 5,
    "Brazil": 5,
    "Poland": 5,
    "Portugal": 5,
    "Thailand": 5,
    "United Arab Emirates": 5,
    "Bulgaria": 4,
    "Cambodia": 4,
    "Colombia": 4,
    "Denmark": 4,
    "Israel": 4,
    "South Africa": 4,
    "Albania": 3,
    "Cyprus": 3,
    "Ghana": 3,
    "Hungary": 3,
    "Indonesia": 3,
    "Ireland": 3,
    "Korea, Republic of": 3,
    "New Zealand": 3,
    "Qatar": 3,
    "Romania": 3,
    "Russia": 3,
    "Argentina": 2,
    "Belgium": 2,
    "Dominican Republic": 2,
    "Egypt": 2,
    "Honduras": 2,
    "Oman": 2,
    "Peru": 2,
    "Switzerland": 2,
    "Vietnam": 2,
    "Armenia": 1,
    "Botswana": 1,
    "Ecuador": 1,
    "Estonia": 1,
    "Guatemala": 1,
    "Latvia": 1,
    "Lebanon": 1,
    "Luxembourg": 1,
    "Macau": 1,
    "Morocco": 1,
    "Nigeria": 1,
    "Serbia": 1,
}

# =========================
# ONLY COUNT "DOWNLOADS" (APP UNITS)
# =========================
DOWNLOAD_PRODUCT_TYPES = {
    "1", "1F", "1T", "1E", "1EP", "1EU", "1-B",
    "F1", "F1-B",
}

# =========================
# PRODUCT TYPE LABELS (readable skipped output)
# =========================
PRODUCT_TYPE_LABELS = {
    "1":   "App (iOS/iPadOS/visionOS/watchOS)",
    "1F":  "App (Universal, excl. tvOS)",
    "1T":  "App (tvOS)",
    "1E":  "App (Custom iOS app)",
    "1EP": "App (Custom iPadOS app)",
    "1EU": "App (Custom universal app)",
    "1-B": "App Bundle (iOS/iPadOS/visionOS)",
    "F1":  "App (Mac)",
    "F1-B":"App Bundle (Mac)",
    "3":   "Redownload",
    "3F":  "Redownload (Universal, excl. tvOS)",
    "7":   "Update",
    "7F":  "Update (Universal, excl. tvOS)",
    "7T":  "Update (tvOS)",
    "IA1": "In-App Purchase",
    "IA9": "In-App Subscription",
    "IAY": "Auto-Renewable Subscription",
    "FI1": "In-App Purchase (Mac)",
}

def label_product_type(code: str) -> str:
    code = (code or "").strip()
    if not code:
        return "BLANK – (Unknown/Blank Product Type)"
    desc = PRODUCT_TYPE_LABELS.get(code)
    return f"{code} – {desc}" if desc else f"{code} – (Unknown Product Type)"

# =========================
# COUNTRY CODE -> NAME
# =========================
COUNTRY_CODES = {
    "US": "United States",
    "NO": "Norway",
    "CN": "China mainland",
    "CA": "Canada",
    "GB": "United Kingdom",
    "IN": "India",
    "DE": "Germany",
    "IT": "Italy",
    "AU": "Australia",
    "FR": "France",
    "JP": "Japan",
    "ES": "Spain",
    "TW": "Taiwan",
    "NL": "Netherlands",
    "SG": "Singapore",
    "HK": "Hong Kong",
    "MY": "Malaysia",
    "MX": "Mexico",
    "SA": "Saudi Arabia",
    "UA": "Ukraine",
    "GR": "Greece",
    "PH": "Philippines",
    "SE": "Sweden",
    "TR": "Türkiye",
    "AT": "Austria",
    "BR": "Brazil",
    "TH": "Thailand",
    "AE": "United Arab Emirates",
    "BG": "Bulgaria",
    "KH": "Cambodia",
    "CO": "Colombia",
    "DK": "Denmark",
    "IL": "Israel",
    "PL": "Poland",
    "PT": "Portugal",
    "ZA": "South Africa",
    "AL": "Albania",
    "CY": "Cyprus",
    "GH": "Ghana",
    "HU": "Hungary",
    "ID": "Indonesia",
    "KR": "Korea, Republic of",
    "NZ": "New Zealand",
    "QA": "Qatar",
    "RO": "Romania",
    "RU": "Russia",
    "AR": "Argentina",
    "BE": "Belgium",
    "DO": "Dominican Republic",
    "EG": "Egypt",
    "HN": "Honduras",
    "IE": "Ireland",
    "OM": "Oman",
    "PE": "Peru",
    "CH": "Switzerland",
    "VN": "Vietnam",
    "AM": "Armenia",
    "BW": "Botswana",
    "EC": "Ecuador",
    "EE": "Estonia",
    "GT": "Guatemala",
    "LV": "Latvia",
    "LB": "Lebanon",
    "LU": "Luxembourg",
    "MO": "Macau",
    "MA": "Morocco",
    "NG": "Nigeria",
    "RS": "Serbia",
}

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
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

# =========================
# HISTORIKK-FIL
# =========================
history_file = "data/asc_history.json"
os.makedirs("data", exist_ok=True)

try:
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)
except FileNotFoundError:
    history = {
        "last_data_update": "",
        "total_units_all_time": BASELINE_TOTAL_UNITS_ALL_TIME,
        "total_country_downloaded_all_time": len([k for k, v in BASELINE_TOTAL_PER_COUNTRY.items() if int(v) > 0]),
        "total_per_country": dict(sorted(BASELINE_TOTAL_PER_COUNTRY.items(), key=lambda x: -x[1])),
        "days": []
    }

history.setdefault("days", [])
history.setdefault("total_per_country", {})
history.setdefault("total_units_all_time", BASELINE_TOTAL_UNITS_ALL_TIME)
history.setdefault("total_country_downloaded_all_time", 0)
history.setdefault("last_data_update", "")

# =========================
# HOPP OVER DAGEN HVIS DEN ALLEREDE ER REGISTRERT
# =========================
if any(d.get("report_date") == yesterday for d in history["days"]):
    print(f"Data for {yesterday} er allerede registrert. Ingen oppdatering gjort.")
    raise SystemExit(0)

# =========================
# FETCH SALES REPORT (YESTERDAY)
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
    raise Exception(f"Sales API HTTP error {sales_response.status_code}:\n{sales_response.text}")

content_type = (sales_response.headers.get("Content-Type", "") or "").lower()
if "gzip" in content_type or sales_response.content[:2] == b"\x1f\x8b":
    sales_report_text = gzip.decompress(sales_response.content).decode("utf-8")
else:
    raise Exception(f"Sales API returned non-gzip response:\n{sales_response.text}")

# =========================
# PARSE SALES TSV
# =========================
def parse_units(value) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0

total_units_today = 0
downloads_by_country_code = {}
downloads_by_device = {}

skipped_readable = {}
negative_rows = []

tsv_io = StringIO(sales_report_text)
reader = csv.DictReader(tsv_io, delimiter="\t")

for row in reader:
    product_type = (row.get("Product Type Identifier") or "").strip()
    units = parse_units(row.get("Units"))

    country_code = (row.get("Country Code") or "").strip() or "UNKNOWN"
    device = (row.get("Device") or "").strip() or "UNKNOWN"

    # Integrity check: abort on ANY negative units
    if units < 0:
        negative_rows.append({
            "product_type": product_type,
            "units": units,
            "country_code": country_code,
            "device": device,
            "title": (row.get("Title") or "").strip(),
            "sku": (row.get("SKU") or "").strip(),
        })
        continue

    # Count only downloads/app units
    if product_type in DOWNLOAD_PRODUCT_TYPES:
        total_units_today += units
        downloads_by_country_code[country_code] = downloads_by_country_code.get(country_code, 0) + units
        downloads_by_device[device] = downloads_by_device.get(device, 0) + units
    else:
        if units != 0:
            key = label_product_type(product_type)
            skipped_readable[key] = skipped_readable.get(key, 0) + units

# Abort without writing JSON if negative units exist
if negative_rows:
    print("INTEGRITY CHECK FAILED: Negative units found in report. No update written.")
    for r in negative_rows:
        print(
            f"  product_type={r['product_type'] or 'BLANK'} units={r['units']} "
            f"country={r['country_code']} device={r['device']} title={r['title']} sku={r['sku']}"
        )
    raise SystemExit(2)

# Integrity check: totals must match breakdown sums
sum_by_country = sum(int(v) for v in downloads_by_country_code.values())
sum_by_device = sum(int(v) for v in downloads_by_device.values())
if total_units_today != sum_by_country or total_units_today != sum_by_device:
    print("INTEGRITY CHECK FAILED: Totals do not match breakdown sums. No update written.")
    print(f"  total_units_today={total_units_today}")
    print(f"  sum_by_country={sum_by_country}")
    print(f"  sum_by_device={sum_by_device}")
    raise SystemExit(3)

# =========================
# DAGENS ENTRY
# =========================
day_entry = {
    "report_date": yesterday,
    "total_units": total_units_today,
    "sales_by_country": downloads_by_country_code,
    "sales_by_device": downloads_by_device,
    "skipped_units_by_product_type": dict(sorted(skipped_readable.items(), key=lambda x: -abs(x[1]))),
}
history["days"].append(day_entry)

# =========================
# REBEREGN TOTALER (baseline + sum(days))
# =========================
sum_days_units = sum(int(d.get("total_units", 0)) for d in history["days"])
history["total_units_all_time"] = BASELINE_TOTAL_UNITS_ALL_TIME + sum_days_units

# Per country: baseline + sum(days.sales_by_country)
total_per_country = dict(BASELINE_TOTAL_PER_COUNTRY)  # copy
for d in history["days"]:
    per_cc = d.get("sales_by_country", {}) or {}
    for cc, units in per_cc.items():
        country_name = COUNTRY_CODES.get(cc, cc)
        total_per_country[country_name] = total_per_country.get(country_name, 0) + int(units)

history["total_per_country"] = dict(sorted(total_per_country.items(), key=lambda x: -x[1]))

# NEW: number of countries with at least 1 download
history["total_country_downloaded_all_time"] = sum(1 for _, v in history["total_per_country"].items() if int(v) > 0)

# =========================
# SKRIV FIL
# =========================
history["last_data_update"] = yesterday

with open(history_file, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)

print(f"ASC history updated: {total_units_today} downloads added for {yesterday}")
print(f"Total downloads all time (baseline + days): {history['total_units_all_time']}")
print(f"Countries downloaded all time: {history['total_country_downloaded_all_time']}")
if skipped_readable:
    print("Filtered out units (non-download product types):")
    for k, v in sorted(skipped_readable.items(), key=lambda x: -abs(x[1])):
        print(f"  {k}: {v}")

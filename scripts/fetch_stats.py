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
# ONLY COUNT "DOWNLOADS" (APP UNITS)
# =========================
# Product Type Identifiers for apps (exclude updates=7, redownloads=3, IAP=IA*, etc.)
# Source: Apple "Product type identifiers" reference.
DOWNLOAD_PRODUCT_TYPES = {
    "1",    # Free or paid app (iOS/iPadOS/visionOS/watchOS)
    "1F",   # Free or paid app (Universal app, excluding tvOS)
    "1T",   # tvOS app
    "1E",   # Paid app (Custom iOS app)
    "1EP",  # Paid app (Custom iPadOS app)
    "1EU",  # Paid app (Custom universal app)
    "1-B",  # App bundle (iOS/iPadOS/visionOS bundle)
    "F1",   # Free or paid app (Mac)  (appears in Apple's list; keep if you ship Mac)
    "F1-B", # Mac app bundle
}

# =========================
# Landkode til navn mapping
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
    "QA": "Qatar",
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
    # STARTTOTAL før første kjøring
    history = {
        "last_data_update": yesterday,
        "total_units_all_time": 852,
        "total_per_country": {
            "United States": 305,
            "Norway": 93,
            "China mainland": 48,
            "Canada": 27,
            "United Kingdom": 26,
            "India": 25,
            "Germany": 23,
            "Italy": 22,
            "Australia": 16,
            "France": 16,
            "Japan": 16,
            "Spain": 14,
            "Taiwan": 14,
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
            "Thailand": 5,
            "United Arab Emirates": 5,
            "Bulgaria": 4,
            "Cambodia": 4,
            "Colombia": 4,
            "Denmark": 4,
            "Israel": 4,
            "Poland": 4,
            "Portugal": 4,
            "South Africa": 4,
            "Albania": 3,
            "Cyprus": 3,
            "Ghana": 3,
            "Hungary": 3,
            "Indonesia": 3,
            "Korea, Republic of": 3,
            "New Zealand": 3,
            "Romania": 3,
            "Russia": 3,
            "Argentina": 2,
            "Belgium": 2,
            "Dominican Republic": 2,
            "Egypt": 2,
            "Honduras": 2,
            "Ireland": 2,
            "Oman": 2,
            "Peru": 2,
            "Qatar": 2,
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
            "Serbia": 1
        },
        "days": []
    }

# =========================
# (VALGFRITT, MEN SMART): LÅS EN BASELINE SÅ TOTALEN IKKE DRIVER
# =========================
# Hvis baseline ikke finnes (eldre filer), lag den slik at totalen din bevares:
# baseline + sum(days) == total_units_all_time
if "baseline_total_units_all_time" not in history:
    summed_days = sum(int(d.get("total_units", 0)) for d in history.get("days", []))
    history["baseline_total_units_all_time"] = int(history.get("total_units_all_time", 0)) - summed_days

# =========================
# HOPP OVER DAGEN HVIS DEN ALLEREDE ER REGISTRERT
# =========================
if any(d.get("report_date") == yesterday for d in history.get("days", [])):
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
# PARSE SALES TSV (COUNT ONLY DOWNLOAD PRODUCT TYPES)
# =========================
def parse_units(value) -> int:
    # Units kan komme som "2" eller "2.0" (rapportfeltet er DECIMAL i Apple docs)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0

sales_data = []
total_units_today = 0

tsv_io = StringIO(sales_report_text)
reader = csv.DictReader(tsv_io, delimiter="\t")

skipped_by_type = {}  # debug: viser hva som ble filtrert bort

for row in reader:
    product_type = (row.get("Product Type Identifier") or "").strip()
    units = parse_units(row.get("Units"))

    # Filtrer vekk alt som ikke er "app download/app unit"
    if product_type not in DOWNLOAD_PRODUCT_TYPES:
        if units != 0:
            skipped_by_type[product_type] = skipped_by_type.get(product_type, 0) + units
        continue

    total_units_today += units
    sales_data.append({
        "country_code": (row.get("Country Code") or "").strip(),
        "product_type": product_type,
        "units": units,
        "device": (row.get("Device") or "").strip(),
        "platform": (row.get("Supported Platforms") or "").strip(),
    })

# =========================
# DAGENS DOWNLOADS PER LAND (bruk Country Code)
# =========================
sales_by_country = {}
for entry in sales_data:
    cc = entry["country_code"] or "UNKNOWN"
    sales_by_country[cc] = sales_by_country.get(cc, 0) + entry["units"]

# =========================
# OPPDATER TOTAL PER LAND
# =========================
history.setdefault("total_per_country", {})
for country_code, units in sales_by_country.items():
    country_name = COUNTRY_CODES.get(country_code, country_code)
    history["total_per_country"][country_name] = history["total_per_country"].get(country_name, 0) + units

# =========================
# DAGENS DOWNLOADS PER ENHET
# =========================
sales_by_device = {}
for entry in sales_data:
    device = entry["device"] or "UNKNOWN"
    sales_by_device[device] = sales_by_device.get(device, 0) + entry["units"]

# =========================
# DAGENS ENTRY
# =========================
day_entry = {
    "report_date": yesterday,
    "total_units": total_units_today,
    "sales_by_country": sales_by_country,
    "sales_by_device": sales_by_device,
    # Valgfritt men nyttig for feilsøking: hva ble filtrert bort?
    "skipped_units_by_product_type": dict(sorted(skipped_by_type.items(), key=lambda x: -abs(x[1]))),
}

history.setdefault("days", [])
history["days"].append(day_entry)

# =========================
# REBEREGN TOTAL (baseline + sum(days)) SÅ TOTALEN ALLTID ER KONSISTENT
# =========================
history["total_units_all_time"] = int(history.get("baseline_total_units_all_time", 0)) + sum(
    int(d.get("total_units", 0)) for d in history["days"]
)

# =========================
# SORTER TOTAL PER LAND
# =========================
history["total_per_country"] = dict(
    sorted(history["total_per_country"].items(), key=lambda x: -x[1])
)

# =========================
# SKRIV FIL
# =========================
history["last_data_update"] = yesterday

with open(history_file, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)

print(f"ASC history updated: {total_units_today} downloads added for {yesterday}")
print(f"Total downloads all time: {history['total_units_all_time']}")
if skipped_by_type:
    print("Filtered out units (non-download product types):")
    for k, v in sorted(skipped_by_type.items(), key=lambda x: -abs(x[1])):
        print(f"  {k or 'BLANK'}: {v}")

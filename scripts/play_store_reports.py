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
PREFIX = "stats/installs/"
OUTPUT_FILE = "data/play_store_history.json"

# =========================
# LANDKODER → NAVN
# =========================
COUNTRY_MAP = {
    "US": "United States",
    "NO": "Norway",
    "CN": "China mainland",
    "CA": "Canada",
    "CL": "Chile",
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
    "KW": "Kuwait",
    "IQ": "Iraq",
    "DZ": "Algeria",
    "JO": "Jordan",
    "TN": "Tunisia",
    "YE": "Yemen",
    "LY": "Libya",
    "MR": "Mauritania",
    "KE": "Kenya",
    "ME": "Montenegro",
    "LK": "Sri Lanka",
    "BH": "Bahrain",
    "FI": "Finland",
    "BN": "Brunei",
    "SN": "Senegal",
    "GE": "Georgia",
    "PK": "Pakistan",
    "BJ": "Benin",
    "BO": "Bolivia",
    "MK": "North Macedonia",
    "ML": "Mali",
    "MM": "Myanmar",
    "MZ": "Mozambique",
    "PA": "Panama",
    "VE": "Venezuela",
    "ZW": "Zimbabwe",
    "T\u00fcrkiye": "Turkey"
}

# =========================
# LAST UPDATED
# =========================
last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# =========================
# INIT STORAGE
# =========================
client = storage.Client.from_service_account_json(
    os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
)

bucket = client.bucket(BUCKET_NAME)

# =========================
# HENT ALLE FILER
# =========================
blobs = list(bucket.list_blobs(prefix=PREFIX))
country_files = [b for b in blobs if "country.csv" in b.name]

print(f"Fant {len(country_files)} filer")

all_data = []

# =========================
# LES ALLE CSV-FILER
# =========================
for blob in country_files:
    print("Leser:", blob.name)

    content = blob.download_as_text()
    df = pd.read_csv(StringIO(content))

    # Rens kolonner
    df.columns = [c.strip() for c in df.columns]

    # Kun relevante kolonner
    df = df[["Country", "Daily Device Installs"]]

    all_data.append(df)

# =========================
# KOMBINER DATA
# =========================
df_all = pd.concat(all_data)

# Numerisk trygghet
df_all["Daily Device Installs"] = pd.to_numeric(df_all["Daily Device Installs"])

# =========================
# SUMMER PER LAND
# =========================
by_country = df_all.groupby("Country")["Daily Device Installs"].sum().to_dict()

# Fjern nuller
by_country = {k: int(v) for k, v in by_country.items() if v > 0}

# Konverter til navn
by_country_named = {
    COUNTRY_MAP.get(k, k): v
    for k, v in by_country.items()
}

# Sorter
by_country_named = dict(
    sorted(by_country_named.items(), key=lambda x: x[1], reverse=True)
)

# Total installs
total_installs = sum(by_country.values())

# =========================
# OUTPUT
# =========================
result = {
    "last_updated": last_updated,
    "total_downloads": int(total_installs),
    "by_country": by_country_named
}

os.makedirs("data", exist_ok=True)

with open(OUTPUT_FILE, "w") as f:
    json.dump(result, f, indent=2)

# =========================
# LOGGING
# =========================
print("\n✅ FERDIG")
print("🕒 Last updated:", last_updated)
print("📦 Total installs:", total_installs)
print("🌍 Land:", len(by_country_named))

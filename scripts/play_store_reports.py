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
    "AE": "United Arab Emirates",
    "AU": "Australia",
    "BG": "Bulgaria",
    "BJ": "Benin",
    "BR": "Brazil",
    "CA": "Canada",
    "CN": "China",
    "EG": "Egypt",
    "ES": "Spain",
    "FR": "France",
    "HK": "Hong Kong",
    "ID": "Indonesia",
    "IN": "India",
    "IQ": "Iraq",
    "JP": "Japan",
    "KR": "South Korea",
    "LY": "Libya",
    "MA": "Morocco",
    "ML": "Mali",
    "MM": "Myanmar",
    "MY": "Malaysia",
    "NG": "Nigeria",
    "NL": "Netherlands",
    "NO": "Norway",
    "PH": "Philippines",
    "PK": "Pakistan",
    "PS": "Palestine",
    "PT": "Portugal",
    "QA": "Qatar",
    "SA": "Saudi Arabia",
    "SG": "Singapore",
    "TH": "Thailand",
    "TR": "Turkey",
    "TW": "Taiwan",
    "US": "United States",
    "VE": "Venezuela",
    "VN": "Vietnam",
    "ZW": "Zimbabwe",
    "LK": "Sri Lanka"
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

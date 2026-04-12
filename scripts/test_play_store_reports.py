import os
import json
import pandas as pd
from google.cloud import storage
from io import StringIO

BUCKET_NAME = "pubsite_prod_4639390102037107647"
PREFIX = "stats/installs/"
OUTPUT_FILE = "data/play_store_history.json"

client = storage.Client.from_service_account_json(
    os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
)

bucket = client.bucket(BUCKET_NAME)

# Finn riktig fil (country)
blobs = list(bucket.list_blobs(prefix=PREFIX))
country_files = [b for b in blobs if "country.csv" in b.name]

if not country_files:
    print("Fant ingen country-filer")
    exit(1)

# Ta nyeste fil
latest_blob = sorted(country_files, key=lambda b: b.name, reverse=True)[0]
print("Bruker fil:", latest_blob.name)

# Last ned CSV
content = latest_blob.download_as_text()
df = pd.read_csv(StringIO(content))

print("\nKolonner i CSV:", df.columns.tolist())

# === FINN RIKTIG KOLONNER ===
# Typisk: country_code + installs
country_col = [c for c in df.columns if "country" in c.lower()][0]
install_col = [c for c in df.columns if "install" in c.lower()][0]

# Summer installs per land
by_country = df.groupby(country_col)[install_col].sum().to_dict()
total_installs = int(df[install_col].sum())

# === OUTPUT ===
result = {
    "total_installs": total_installs,
    "by_country": by_country
}

os.makedirs("data", exist_ok=True)

with open(OUTPUT_FILE, "w") as f:
    json.dump(result, f, indent=2)

print("\n✅ Ferdig!")
print("Total installs:", total_installs)
print("Antall land:", len(by_country))

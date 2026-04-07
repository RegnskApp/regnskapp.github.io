import os
import json
import pandas as pd
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account
from io import StringIO

# === KONFIGURASJON ===
PACKAGE_NAME = "com.balancetrackr.app"
OUTPUT_FILE = "data/play_store_history.json"
SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]

SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

# === AUTENTISERING ===
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("androidpublisher", "v3", credentials=credentials)

# === HENT RAPPORTER FRA PLAY STORE ===
try:
    reports = service.reports().list(
        packageName=PACKAGE_NAME,
        reportType="statistics"  # acquisition/install stats
    ).execute()

    total_installs = 0
    by_country = {}

    for report in reports.get("downloads", []):
        url = report.get("url")
        if not url:
            continue

        # Hent CSV/TSV
        r = requests.get(url)
        r.raise_for_status()
        # CSV kan være tab-separated
        df = pd.read_csv(StringIO(r.text), sep="\t")

        # summer per land
        if "country" in df.columns and "installs" in df.columns:
            country_installs = df.groupby("country")["installs"].sum().to_dict()
            for country, installs in country_installs.items():
                by_country[country] = by_country.get(country, 0) + installs
            total_installs += df["installs"].sum()

except Exception as e:
    print("Feil ved henting av Play Store data:", e)
    by_country = {}
    total_installs = 0

# === LAG JSON OUTPUT ===
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
output_data = {
    "total_installs": int(total_installs),
    "by_country": by_country
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(output_data, f, indent=2)

print("Data oppdatert:", output_data)

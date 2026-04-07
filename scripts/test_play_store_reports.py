# scripts/test_play_store_reports.py
import os
from google.cloud import storage

# Bucket og prefix
BUCKET_NAME = "pubsite_prod_4639390102037107647"
PREFIX = "stats/installs/"

# Autentisering via GitHub Secret
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
bucket = client.bucket(BUCKET_NAME)

try:
    blobs = list(bucket.list_blobs(prefix=PREFIX))
    if not blobs:
        print("Ingen filer funnet i bucket under prefix:", PREFIX)
    else:
        print("Følgende filer finnes i bucket:")
        for blob in blobs:
            print("-", blob.name)
except Exception as e:
    print("Feil ved henting av rapporter:", e)

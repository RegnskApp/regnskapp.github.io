from google.cloud import storage
import os

BUCKET_NAME = "pubsite_prod_4639390102037107647"
PREFIX = "stats/installs/"

try:
    client = storage.Client.from_service_account_json(
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    )
    bucket = client.bucket(BUCKET_NAME)

    blobs = list(bucket.list_blobs(prefix=PREFIX, max_results=5))

    if not blobs:
        print("⚠️ Ingen filer funnet (eller fortsatt ikke tilgang)")
    else:
        print(f"✅ OK! Fant {len(blobs)} filer (viser maks 5):\n")
        for blob in blobs:
            print("-", blob.name)

except Exception as e:
    print("❌ FEIL:", e)

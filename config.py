import os

# Routes for MoSPI Airfare Basket (Expanded to capture Akasa Air & PS suggestions)
ROUTES = [
    {"origin": "DEL", "destination": "BOM"},
    {"origin": "BOM", "destination": "DEL"},
    {"origin": "DEL", "destination": "BLR"},
    {"origin": "BLR", "destination": "DEL"},
    {"origin": "MAA", "destination": "DEL"},
    {"origin": "BOM", "destination": "BLR"}, # High Akasa Air frequency route
    {"origin": "DEL", "destination": "CCU"}  # PS Suggested route
]

# Advance Purchase Windows (Added T+45 per PS requirement)
T_WINDOWS = [1, 7, 15, 30, 45]

# Storage Paths
DATA_DIR = os.getenv("DATA_DIR", "data")
MASTER_DATASET_PATH = os.path.join(DATA_DIR, "master_dataset.csv")
CLEANED_DATASET_PATH = os.path.join(DATA_DIR, "cleaned_dataset.csv")
CPI_REPORT_PATH = os.path.join(DATA_DIR, "mospi_cpi_report.csv")

# Proxy Settings (Disabled for local cron execution)
USE_PROXY = False
PROXY_SERVER = ""

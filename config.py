import os

# Routes for MoSPI Airfare Basket
ROUTES = [
    {"origin": "DEL", "destination": "BOM"},
    {"origin": "BOM", "destination": "DEL"},
    {"origin": "DEL", "destination": "BLR"},
    {"origin": "BLR", "destination": "DEL"},
    {"origin": "MAA", "destination": "DEL"},
]

# Advance Purchase Windows
T_WINDOWS = [1, 7, 15, 30]

# Storage Paths
DATA_DIR = os.getenv("DATA_DIR", "data")
MASTER_DATASET_PATH = os.path.join(DATA_DIR, "master_dataset.csv")
CLEANED_DATASET_PATH = os.path.join(DATA_DIR, "cleaned_dataset.csv")
CPI_REPORT_PATH = os.path.join(DATA_DIR, "mospi_cpi_report.csv")

# Cloud Proxy Configuration
# Set USE_PROXY=true in production environment variables
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
PROXY_SERVER = os.getenv("PROXY_SERVER", "") # Format: http://user:pass@host:port
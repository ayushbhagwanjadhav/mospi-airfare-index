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
USE_PROXY = True
PROXY_SERVER = "http://sbhqqwvw:5ozc8y1elhxn@31.59.20.176:6754/"

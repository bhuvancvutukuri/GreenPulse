import os
import pandas as pd
import requests

DROPBOX_URL = "https://www.dropbox.com/scl/fi/66a75b2bww1v8skk15rft/2015_Street_Tree_Census_-_Tree_Data_20241207.csv?rlkey=1n6g0og9xl1cszlpggdl0ibpo&st=mghmm092&dl=1"

RAW_PATH = "data/raw/ny_trees_raw.csv"
PROCESSED_PATH = "data/processed/trees_clean.csv"

COLUMNS_TO_DROP = [
    "x_sp", "y_sp", "bin", "bbl", "state", "spc_latin", "user_type",
    "borocode", "boro_ct", "census tract", "steward", "guards",
    "sidewalk", "problems", "council district"
]

def ensure_dirs():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

def download_raw():
    print("Downloading raw dataset...")
    r = requests.get(DROPBOX_URL, timeout=120)
    r.raise_for_status()
    with open(RAW_PATH, "wb") as f:
        f.write(r.content)
    print(f"Saved raw CSV -> {RAW_PATH}")

def clean_data(sample_frac=0.01, random_state=42):
    print("Loading raw CSV...")
    df = pd.read_csv(RAW_PATH)

    # sample to reduce compute (same as your notebook)
    df = df.sample(frac=sample_frac, random_state=random_state).reset_index(drop=True)

    # Fill missing categorical fields
    for col in ["spc_common", "health", "curb_loc"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    # Convert types
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    for col in ["tree_dbh", "stump_diam"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # standardize categories
    for col in ["health", "status", "spc_common", "borough"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()

    # Remove outliers (IQR) on tree_dbh
    if "tree_dbh" in df.columns:
        q1 = df["tree_dbh"].quantile(0.25)
        q3 = df["tree_dbh"].quantile(0.75)
        iqr = q3 - q1
        df = df[(df["tree_dbh"] >= (q1 - 1.5 * iqr)) & (df["tree_dbh"] <= (q3 + 1.5 * iqr))]

    # postcode numeric
    if "postcode" in df.columns:
        df["postcode"] = pd.to_numeric(df["postcode"], errors="coerce")

    # Drop columns if present
    drop_existing = [c for c in COLUMNS_TO_DROP if c in df.columns]
    df = df.drop(columns=drop_existing, errors="ignore")

    # Keep only rows with lat/lon if present (helps maps)
    if "latitude" in df.columns and "longitude" in df.columns:
        df = df.dropna(subset=["latitude", "longitude"])

    print(f"Cleaned rows: {df.shape[0]}, cols: {df.shape[1]}")
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Saved processed CSV -> {PROCESSED_PATH}")

if __name__ == "__main__":
    ensure_dirs()
    if not os.path.exists(RAW_PATH):
        download_raw()
    clean_data()

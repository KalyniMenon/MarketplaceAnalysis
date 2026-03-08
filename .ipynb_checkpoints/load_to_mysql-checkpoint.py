"""
Airbnb Marketplace Analysis
Phase 1: Clean & Load Data into MySQL
-------------------------------------
Run this script once to clean your CSV files and load them into MySQL.

Requirements:
    pip install pandas sqlalchemy pymysql
"""

import pandas as pd
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────
# CONFIG — update your MySQL password here
# ─────────────────────────────────────────────
MYSQL_USER     = "root"
MYSQL_PASSWORD = "KalyaniMenon!1998"   # ← change this
MYSQL_HOST     = "localhost"
MYSQL_PORT     = 3306
MYSQL_DB       = "airbnb_analysis"

# File paths
FILES = {
    "berlin": {
        "listings": r"C:\Users\Victus\Desktop\Data_Analyst\PowerBIprojects\MarketplaceAnalysis\Berlin\listings.csv.gz",
        "calendar": r"C:\Users\Victus\Desktop\Data_Analyst\PowerBIprojects\MarketplaceAnalysis\Berlin\calendar.csv.gz",
    },
    "amsterdam": {
        "listings": r"C:\Users\Victus\Desktop\Data_Analyst\PowerBIprojects\MarketplaceAnalysis\Amsterdam\listings.csv.gz",
        "calendar": r"C:\Users\Victus\Desktop\Data_Analyst\PowerBIprojects\MarketplaceAnalysis\Amsterdam\calendar.csv.gz",
    },
}

# ─────────────────────────────────────────────
# HELPER: clean price columns like "$1,200.00"
# ─────────────────────────────────────────────
def clean_price(series):
    return (
        series.astype(str)
        .str.replace(r"[\$,]", "", regex=True)
        .str.strip()
        .replace("nan", None)
        .astype(float)
    )


# ─────────────────────────────────────────────
# CLEAN LISTINGS
# ─────────────────────────────────────────────
def clean_listings(path, city):
    print(f"  Loading listings for {city}...")
    df = pd.read_csv(path, compression="infer", low_memory=False)

    # Keep only useful columns
    cols = [
        "id", "host_id", "neighbourhood_cleansed", "room_type",
        "price", "minimum_nights", "number_of_reviews",
        "review_scores_rating", "latitude", "longitude", "availability_365"
    ]
    # Only keep columns that exist in this file
    cols = [c for c in cols if c in df.columns]
    df = df[cols].copy()

    # Rename for clarity
    df.rename(columns={
        "id": "listing_id",
        "neighbourhood_cleansed": "neighbourhood"
    }, inplace=True)

    # Clean price
    if "price" in df.columns:
        df["price"] = clean_price(df["price"])

    # Add city
    df["city"] = city

    # Drop rows with no listing_id or price
    df.dropna(subset=["listing_id", "price"], inplace=True)
    df["listing_id"] = df["listing_id"].astype(int)

    print(f"    → {len(df):,} listings loaded for {city}")
    return df


# ─────────────────────────────────────────────
# CLEAN CALENDAR
# ─────────────────────────────────────────────
def clean_calendar(path, city):
    print(f"  Loading calendar for {city}...")
    df = pd.read_csv(path, compression="infer", low_memory=False)

    cols = ["listing_id", "date", "available", "price"]
    cols = [c for c in cols if c in df.columns]
    df = df[cols].copy()

    # Clean price
    if "price" in df.columns:
        df["price"] = clean_price(df["price"])

    # Convert available to boolean int (1/0)
    if "available" in df.columns:
        df["available"] = df["available"].map({"t": 1, "f": 0, True: 1, False: 0})

    # Parse date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Add city
    df["city"] = city

    df.dropna(subset=["listing_id", "date"], inplace=True)
    df["listing_id"] = df["listing_id"].astype(int)

    print(f"    → {len(df):,} calendar rows loaded for {city}")
    return df


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    # 1. Create MySQL engine
    engine = create_engine(
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/",
        echo=False
    )

    # 2. Create database if not exists
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}"))
        print(f"✓ Database '{MYSQL_DB}' ready")

    # Reconnect to the specific DB
    engine = create_engine(
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}",
        echo=False
    )

    # 3. Load and clean all cities
    all_listings = []
    all_calendar = []

    for city, paths in FILES.items():
        all_listings.append(clean_listings(paths["listings"], city))
        all_calendar.append(clean_calendar(paths["calendar"], city))

    listings_df = pd.concat(all_listings, ignore_index=True)
    calendar_df = pd.concat(all_calendar, ignore_index=True)

    # 4. Write to MySQL
    print("\nWriting to MySQL...")
    listings_df.to_sql("listings", engine, if_exists="replace", index=False, chunksize=1000)
    print(f"✓ listings table: {len(listings_df):,} rows")

    calendar_df.to_sql("calendar", engine, if_exists="replace", index=False, chunksize=5000)
    print(f"✓ calendar table: {len(calendar_df):,} rows")

    print("\n✅ Done! Your data is in MySQL.")
    print(f"   Database : {MYSQL_DB}")
    print(f"   Tables   : listings, calendar")
    print("\nNext step: Run the KPI SQL views (phase2_kpi_views.sql)")


if __name__ == "__main__":
    main()
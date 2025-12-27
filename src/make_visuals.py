import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import requests
import json

PROCESSED_PATH = "data/processed/trees_clean.csv"
GEOJSON_URL = "https://raw.githubusercontent.com/fedhere/PUI2015_EC/refs/heads/master/mam1612_EC/nyc-zip-code-tabulation-areas-polygons.geojson"

def ensure_dirs():
    os.makedirs("visuals", exist_ok=True)

def make_hist(df):
    plt.figure(figsize=(8, 6))
    plt.hist(df["tree_dbh"].dropna(), bins=20, edgecolor="black")
    plt.title("Histogram of Tree DBH")
    plt.xlabel("Tree Diameter (DBH)")
    plt.ylabel("Frequency")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig("visuals/hist_tree_dbh.png", dpi=160)
    plt.close()

def make_violin(df):
    plt.figure(figsize=(8, 6))
    sns.violinplot(x="health", y="tree_dbh", data=df, inner="quartile")
    plt.title("Violin Plot of Tree DBH by Health")
    plt.xlabel("Health")
    plt.ylabel("Tree Diameter (DBH)")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig("visuals/violin_dbh_health.png", dpi=160)
    plt.close()

def make_density(df):
    plt.figure(figsize=(10, 6))
    sns.kdeplot(data=df, x="tree_dbh", hue="borough", fill=True, alpha=0.25)
    plt.title("Density Plot of Tree DBH by Borough")
    plt.xlabel("Tree Diameter (DBH)")
    plt.ylabel("Density")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig("visuals/density_dbh_borough.png", dpi=160)
    plt.close()

def make_choropleth_html(df):
    # tree count per zip
    d = df.dropna(subset=["postcode"]).copy()
    d["postcode"] = d["postcode"].astype(int).astype(str)
    tree_density = d.groupby("postcode").size().reset_index(name="tree_count")

    # geojson
    geo = requests.get(GEOJSON_URL, timeout=60).json()

    fig = px.choropleth_mapbox(
        tree_density,
        geojson=geo,
        locations="postcode",
        featureidkey="properties.postalCode",
        color="tree_count",
        mapbox_style="open-street-map",
        zoom=9,
        center={"lat": df["latitude"].mean(), "lon": df["longitude"].mean()},
        opacity=0.7,
        title="Tree Density by Zip Code"
    )
    fig.write_html("visuals/choropleth_tree_density.html")

if __name__ == "__main__":
    ensure_dirs()
    df = pd.read_csv(PROCESSED_PATH)

    # normalize expected cols
    for col in ["health", "borough"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()

    make_hist(df)
    make_violin(df)
    make_density(df)
    make_choropleth_html(df)

    print("Saved visuals into ./visuals/")

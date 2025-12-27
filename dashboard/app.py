import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table

DATA_PATH = "data/processed/trees_clean.csv"

def load_data():
    df = pd.read_csv(DATA_PATH)

    # normalize
    for col in ["borough", "health", "spc_common"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()

    # safety drops
    if "tree_dbh" in df.columns:
        df = df[df["tree_dbh"].notna()]

    return df

df = load_data()

server = app.server
app.title = "GreenPulse Dashboard"

boroughs = sorted(df["borough"].dropna().unique()) if "borough" in df.columns else []
healths = sorted(df["health"].dropna().unique()) if "health" in df.columns else []

app.layout = html.Div(
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "16px"},
    children=[
        html.H1("GreenPulse: Urban Greenery Dashboard"),
        html.P("Explore NYC street tree health, size, and spatial distribution."),

        html.Div(
            style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
            children=[
                html.Div(
                    style={"minWidth": "240px", "flex": 1},
                    children=[
                        html.Label("Borough"),
                        dcc.Dropdown(
                            id="borough",
                            options=[{"label": b, "value": b} for b in boroughs],
                            value=None,
                            clearable=True,
                            placeholder="All boroughs",
                        ),
                    ],
                ),
                html.Div(
                    style={"minWidth": "240px", "flex": 1},
                    children=[
                        html.Label("Health"),
                        dcc.Dropdown(
                            id="health",
                            options=[{"label": h, "value": h} for h in healths],
                            value=None,
                            clearable=True,
                            placeholder="All health statuses",
                        ),
                    ],
                ),
            ],
        ),

        html.Hr(),

        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
            children=[
                dcc.Graph(id="hist"),
                dcc.Graph(id="bar_avg"),
            ],
        ),

        html.Div(style={"marginTop": "16px"}, children=[dcc.Graph(id="map")]),

        html.Hr(),
        html.H2("Interactive Data Table"),
        dash_table.DataTable(
            id="table",
            columns=[{"name": c, "id": c} for c in df.columns],
            page_size=12,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px", "fontFamily": "Arial"},
            style_header={"fontWeight": "bold", "backgroundColor": "#f0f0f0"},
        ),
    ],
)

@app.callback(
    Output("hist", "figure"),
    Output("bar_avg", "figure"),
    Output("map", "figure"),
    Output("table", "data"),
    Input("borough", "value"),
    Input("health", "value"),
)
def update(borough, health):
    dff = df.copy()

    if borough and "borough" in dff.columns:
        dff = dff[dff["borough"] == borough]
    if health and "health" in dff.columns:
        dff = dff[dff["health"] == health]

    # Histogram
    fig_hist = px.histogram(
        dff, x="tree_dbh", nbins=25,
        title="Tree Diameter (DBH) Distribution"
    )

    # Bar: avg dbh by borough (based on filtered set)
    if "borough" in dff.columns:
        agg = dff.groupby("borough", as_index=False)["tree_dbh"].mean().sort_values("tree_dbh", ascending=False)
        fig_bar = px.bar(agg, x="borough", y="tree_dbh", title="Average Tree DBH by Borough")
    else:
        fig_bar = px.scatter(title="borough column not found")

    # Map
    if {"latitude", "longitude"}.issubset(dff.columns):
        mdf = dff.dropna(subset=["latitude", "longitude"]).copy()
        if len(mdf) > 5000:
            mdf = mdf.sample(5000, random_state=42)

        fig_map = px.scatter_map(
            mdf,
            lat="latitude",
            lon="longitude",
            color="health" if "health" in mdf.columns else None,
            size="tree_dbh",
            size_max=18,
            zoom=9,
            map_style="open-street-map",
            title="Tree Locations (sampled for performance)",
            hover_name="spc_common" if "spc_common" in mdf.columns else None,
            hover_data=[c for c in ["borough", "tree_dbh", "health", "postcode"] if c in mdf.columns],
        )
    else:
        fig_map = px.scatter(title="latitude/longitude columns not found")

    return fig_hist, fig_bar, fig_map, dff.to_dict("records")


if __name__ == "__main__":
    app.run_server(debug=True)

import sys
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.scraper import scrape_catalog
from src.downloader import download_dataset
from src.data_preprocessing import load_data, clean_data
from src.model_training import train_price_model, cluster_hosts
from src.recommendation import build_recommendation_scores, filter_by_preferences
from src.visualizations import parallel_recommendations, radar_for_listing
from src.ui_theme import inject_base_css
from src.data_sources.direct_csv_url_source import DirectCSVURLSource
from src.data_sources.external_site_source import ExternalSiteSource
from src.metrics import compute_metrics

st.set_page_config(page_title="ProPhet-BnB", layout="wide")
inject_base_css()
st.markdown("<h1 style='text-align:center;margin-top:0;'>ProPhet-BnB</h1>", unsafe_allow_html=True)

st.sidebar.header("1. Data Source")
source_mode = st.sidebar.radio(
    "Choose Source Type",
    [
        "InsideAirbnb Snapshot",
        "Local CSV Upload",
        "Direct CSV URL",
        "Website (Custom Scraper)"
    ]
)

uploaded_listings = uploaded_reviews = None
site_url = csv_url = ""
city_entry = None
version = None
custom_url = ""
catalog = None

if source_mode == "InsideAirbnb Snapshot":
    with st.sidebar:
        st.markdown("#### InsideAirbnb City/Date Picker")
        @st.cache_data(show_spinner=False)
        def get_catalog():
            return scrape_catalog()
        try:
            catalog = get_catalog()
        except Exception as e:
            st.error(f"Could not load city catalog: {e}")
            st.stop()
        countries = sorted(catalog.keys())
        country = st.selectbox("Country", countries)
        region = st.selectbox("Region", sorted(catalog[country].keys()))
        city = st.selectbox("City", sorted(catalog[country][region].keys()))
        city_entry = catalog[country][region][city]
        dates = sorted(city_entry.versions.keys(), reverse=True)
        date = st.selectbox("Snapshot Date", dates, index=0)
        st.caption(f"Latest available date: {city_entry.latest_date}")
        force_download = st.checkbox("Force Fresh Download", value=False)
        custom_url = st.text_input("Custom Listings URL (override)", "", placeholder="https://insideairbnb.com/data/.../listings.csv.gz")
        version = city_entry.versions[date]
elif source_mode == "Local CSV Upload":
    uploaded_listings = st.sidebar.file_uploader("Listings CSV", type=["csv"])
    uploaded_reviews = st.sidebar.file_uploader("Reviews CSV (optional)", type=["csv"])
elif source_mode == "Direct CSV URL":
    csv_url = st.sidebar.text_input("Paste Direct CSV URL", "", placeholder="https://.../listings.csv")
elif source_mode == "Website (Custom Scraper)":
    site_url = st.sidebar.text_input("Paste Listing Website Link", "", placeholder="https://www.example.com/listings")
    with st.sidebar.expander("Advanced Scraper Settings"):
        listing_selector = st.text_input("Listing CSS Selector", value=".listing-card")
        price_selector = st.text_input("Price CSS Selector", value=".price")
        name_selector = st.text_input("Name CSS Selector", value=".name")
        image_selector = st.text_input("Image CSS Selector", value="img")

st.sidebar.header("2. Adjust Filters")
default_filters = {
    "price_mode": "Budget",
    "custom_price_range": (0.0, 10000.0),
    "reviews_range": (0, 1000),
    "stars_range": (1.0, 5.0),
    "availability_range": (0, 365),
    "occupancy_group": "Any",
    "suggestions": 6,
    "map_sample": 2000
}
uf = st.session_state.get("user_filters", default_filters.copy())

uf["suggestions"] = st.sidebar.slider("Suggestions to Show", 3, 10, uf.get("suggestions", 6))
uf["price_mode"] = st.sidebar.radio("Price Band", ["Budget", "Comfort", "Premium", "Custom Range"], index=["Budget","Comfort","Premium","Custom Range"].index(uf.get("price_mode", "Budget")))
if uf["price_mode"] == "Custom Range":
    uf["custom_price_range"] = st.sidebar.slider("Custom Price Range [$]", 0.0, 10000.0, uf.get("custom_price_range", (0.0, 10000.0)))
uf["reviews_range"] = st.sidebar.slider("Reviews Count", 0, 1000, uf.get("reviews_range", (0, 1000)))
uf["stars_range"] = st.sidebar.slider("Rating (Stars)", 1.0, 5.0, uf.get("stars_range", (1.0, 5.0)), 0.5)
uf["availability_range"] = st.sidebar.slider("Availability Days", 0, 365, uf.get("availability_range", (0, 365)))
uf["occupancy_group"] = st.sidebar.selectbox("Guest Group", ["Any", "Solo (1)", "Duo (2)", "Small group (3-4)", "Family (5-6)", "Large (7+)"], index=["Any","Solo (1)","Duo (2)","Small group (3-4)","Family (5-6)","Large (7+)"].index(uf.get("occupancy_group", "Any")))
st.session_state["user_filters"] = uf

run_clicked = st.sidebar.button("Analyze Listings", type="primary")

def find_col(df, names):
    """
    Return the first matching column from a list of names, using some fuzzy matching.
    """
    for name in names:
        if name in df.columns:
            return name
    for col in df.columns:
        for name in names:
            if name.lower() in col.lower():
                return col
    return None

def get_numeric_cols(df):
    return [c for c in df.select_dtypes(include='number').columns if df[c].nunique() > 1]

df, source_label = None, ""
max_rows = 10000

def load_dataset():
    if source_mode == "InsideAirbnb Snapshot":
        files = download_dataset(
            version,
            city=city,
            date=date,
            force=force_download,
            override_listings_url=custom_url or None
        )
        df_local = load_data(files["listings"], files["reviews"], files.get("neighbourhoods"))
        df_local = clean_data(df_local)
        meta = {
            "source_label": f"{city} {date}",
            "files": files,
            "mode": "InsideAirbnb"
        }
        return df_local, meta
    if source_mode == "Local CSV Upload":
        if not uploaded_listings:
            st.error("Please upload a listings CSV file.")
            st.stop()
        try:
            df_local = pd.read_csv(uploaded_listings)
        except Exception as e:
            st.error(f"Could not read listings file: {e}")
            st.stop()
        if uploaded_reviews:
            try:
                rev_df = pd.read_csv(uploaded_reviews)
                if "id" in df_local.columns and "listing_id" in rev_df.columns:
                    summary = rev_df.groupby("listing_id").size().rename("num_reviews")
                    df_local = df_local.merge(summary, left_on="id", right_index=True, how="left")
            except Exception as e:
                st.warning(f"Could not read reviews file: {e}")
        df_local = clean_data(df_local)
        return df_local, {"source_label": "Manual Upload", "mode": "LocalCSV"}
    if source_mode == "Direct CSV URL":
        if not csv_url.strip():
            st.error("Please provide a valid CSV URL.")
            st.stop()
        src = DirectCSVURLSource(url=csv_url)
        result = src.load()
        return result.df, {"source_label": "Direct CSV URL", "url": csv_url, "mode": "DirectURL"}
    if source_mode == "Website (Custom Scraper)":
        if not site_url.strip():
            st.error("Please provide a valid listing website link.")
            st.stop()
        src = ExternalSiteSource(
            url=site_url,
            listing_selector=listing_selector,
            field_map={
                "name": {"selector": name_selector, "attr": "text"},
                "price": {"selector": price_selector, "attr": "text"},
                "image_url": {"selector": image_selector, "attr": "src"},
            }
        )
        result = src.load()
        df_local = getattr(result, "df", None)
        if df_local is None or df_local.empty:
            st.error("No listings found. Check your selectors or try a different site.")
            st.stop()
        return df_local, {"source_label": f"Scraped from {site_url}", "mode": "CustomScraper"}
    raise RuntimeError("Unsupported source mode.")

if run_clicked:
    try:
        df, meta = load_dataset()
        source_label = meta.get("source_label", "")
        if df is None or df.empty:
            st.error("No data extracted. Please check your upload/site/link or selectors.")
            st.stop()
        if len(df) > max_rows:
            df = df.sample(max_rows)
            st.warning(f"Sampled {max_rows} rows for performance.")
        try:
            _, df = train_price_model(df)
        except Exception:
            pass
        try:
            _, df = cluster_hosts(df)
        except Exception:
            pass
        df = build_recommendation_scores(df)
        st.session_state["df_base"] = df
        st.session_state["source_label"] = source_label
        st.success(f"Loaded {len(df)} listings!")
    except Exception as e:
        st.error(f"Could not read or process data: {e}")
        st.stop()

df = st.session_state.get("df_base")
source_label = st.session_state.get("source_label", "")

if df is not None:
    st.markdown(f"### Source: {source_label}")

    metrics, price_col = compute_metrics(df)
    def fmt(v): return f"{v:,.1f}" if v is not None and pd.notnull(v) else "—"

    img_col = find_col(df, ["image_url", "Image", "img", "photo", "picture"])
    table_cols = ["id", "name", "neighbourhood", "room_type"]
    for col in [price_col, 'review_scores_rating', img_col]:
        if col and col in df.columns: table_cols.append(col)

    tab_overview, tab_recommend, tab_compare, tab_scatter3d = st.tabs(["Overview", "Recommendations", "Comparison", "3D Scatter Plot"])

    with tab_overview:
        st.markdown("### Overview & Sample")
        st.dataframe(df.head(25)[table_cols], height=350)
        kcols = st.columns(6)
        metrics_display = [
            ("Avg Price", metrics['avg_price']),
            ("Avg Reviews", metrics['avg_reviews']),
            ("Avg Rating", metrics['avg_rating']),
            ("Avg Availability", metrics['avg_availability']),
            ("Avg Amenities", metrics['avg_amenities']),
            ("Listings", metrics['listings'])
        ]
        for (label, val), col in zip(metrics_display, kcols):
            col.metric(label, fmt(val))
        st.write(f"**Active Price Range:** {fmt(metrics['avg_price'])}")

    with tab_recommend:
        st.subheader("Top Suggested Listings")
        recomm_df = df.sort_values("total_score", ascending=False).head(uf["suggestions"])
        rec_cols = [c for c in ["id", "name", "neighbourhood", "room_type", price_col, "review_scores_rating", img_col] if c in recomm_df.columns]
        st.dataframe(recomm_df[rec_cols], height=400)
        st.download_button(
            "Download Suggestions CSV",
            recomm_df[rec_cols].to_csv(index=False),
            file_name="suggestions.csv",
            mime="text/csv"
        )
        st.markdown("### Most Accurate & Optimized Option")
        best_row = recomm_df.iloc[0]
        info = f"**{best_row.get('name', 'Listing')}**"
        if 'neighbourhood' in best_row and pd.notnull(best_row['neighbourhood']):
            info += f" in *{best_row['neighbourhood']}*"
        if price_col in best_row and pd.notnull(best_row[price_col]):
            info += f" (${best_row[price_col]}/night)"
        st.markdown(info)
        if img_col and pd.notnull(best_row[img_col]):
            st.image(best_row[img_col], width=220)
        radar_fig = radar_for_listing(best_row, metrics)
        if radar_fig:
            st.plotly_chart(radar_fig, use_container_width=True)
        st.markdown("#### Why is this the best for you?")
        st.info(
            f"This listing was chosen because it matches your selected price range, guest group, "
            f"and offers strong ratings and amenities. Reason: {best_row.get('recommendation_reason','N/A')}"
        )

    with tab_compare:
        st.subheader("Compare Top Picks (Visual & Images)")
        pfig = parallel_recommendations(recomm_df, max_recs=uf["suggestions"])
        if pfig:
            st.plotly_chart(pfig, use_container_width=True)
        else:
            st.warning("Not enough scoring columns to show parallel recommendations for this dataset.")
        top_n = min(3, len(recomm_df))
        img_cols = st.columns(top_n)
        for idx in range(top_n):
            row = recomm_df.iloc[idx]
            with img_cols[idx]:
                st.markdown(f"**{row.get('name', 'Listing')}**")
                if img_col and pd.notnull(row[img_col]):
                    st.image(row[img_col], width=170)
                price = row.get(price_col, "N/A")
                rating = row.get("review_scores_rating", "N/A")
                location = row.get('neighbourhood', 'N/A')
                amenities = row.get('amenities_count', 'N/A')
                st.caption(f"Price: ${price}, Rating: {rating}, Area: {location}, Amenities: {amenities}")
        def format_listing(x):
            row = recomm_df[recomm_df["id"] == x]
            if not row.empty and "name" in row.columns:
                return f"{row.iloc[0]['name']} ({row.iloc[0]['neighbourhood']})"
            return str(x)
        chosen_id = st.selectbox("Select Listing for Radar", recomm_df["id"], format_func=format_listing)
        rrow = recomm_df[recomm_df["id"] == chosen_id]
        if not rrow.empty:
            rrow = rrow.iloc[0]
            listing_info = f"**{rrow.get('name', 'Listing')}**"
            if 'neighbourhood' in rrow and pd.notnull(rrow['neighbourhood']):
                listing_info += f" in *{rrow['neighbourhood']}*"
            if price_col in rrow and pd.notnull(rrow[price_col]):
                listing_info += f" (${rrow[price_col]}/night)"
            st.markdown(listing_info)
            if img_col and pd.notnull(rrow[img_col]):
                st.image(rrow[img_col], width=180)
            rfig = radar_for_listing(rrow, metrics)
            if rfig:
                st.plotly_chart(rfig, use_container_width=True)

    with tab_scatter3d:
        st.subheader("3D Scatter Plot")
        numeric_cols = get_numeric_cols(df)
        if len(numeric_cols) < 3:
            st.info("Not enough numeric columns for 3D scatter plot.")
        else:
            x_col = st.selectbox("X axis", numeric_cols, index=0, key="3d_x")
            y_col = st.selectbox("Y axis", numeric_cols, index=1 if len(numeric_cols) > 1 else 0, key="3d_y")
            z_col = st.selectbox("Z axis", numeric_cols, index=2 if len(numeric_cols) > 2 else 0, key="3d_z")
            color_col = st.selectbox(
                "Color by",
                [c for c in df.columns if df[c].nunique() < 50 and df[c].dtype == object],
                index=0,
                key="3d_color"
            ) if any(df[c].nunique() < 50 and df[c].dtype == object for c in df.columns) else None
            fig3d = px.scatter_3d(
                df,
                x=x_col,
                y=y_col,
                z=z_col,
                color=color_col,
                hover_name="name" if "name" in df.columns else None,
                hover_data=table_cols,
                title=f"3D Scatter Plot: {x_col} vs {y_col} vs {z_col}",
                height=700
            )
            st.plotly_chart(fig3d, use_container_width=True)
            st.markdown("### Top Listings Visual Comparison (by 3D scatter plot values)")
            top_points = df.sort_values([z_col, y_col, x_col], ascending=False).head(3)
            img_cols = st.columns(3)
            for idx in range(len(top_points)):
                row = top_points.iloc[idx]
                with img_cols[idx]:
                    st.markdown(f"**{row.get('name', 'Listing')}**")
                    if img_col and pd.notnull(row[img_col]):
                        st.image(row[img_col], width=170)
                    price = row.get(price_col, "N/A")
                    rating = row.get("review_scores_rating", "N/A")
                    location = row.get('neighbourhood', 'N/A')
                    amenities = row.get('amenities_count', 'N/A')
                    st.caption(f"Price: ${price}, Rating: {rating}, Area: {location}, Amenities: {amenities}")

else:
    st.info("Paste a data link, pick a city, or upload a CSV, then hit Analyze Listings.")

st.caption("Supports InsideAirbnb, CSVs, direct links, and custom scraping. Use InsideAirbnb or a clean CSV for best results.")
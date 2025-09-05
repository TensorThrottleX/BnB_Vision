import plotly.express as px
import plotly.graph_objects as go

def parallel_recommendations(df, max_recs=6):
    """
    Display a parallel coordinates plot for the top recommendations.
    Uses custom scoring columns if available; falls back to numeric columns.
    """
    scoring = [
        'total_score', 'score_value', 'score_review_quality',
        'score_amenities', 'score_availability', 'availability_365'
    ]
    cols = [c for c in scoring if c in df.columns]
    if len(cols) < 2:
        # Use up to 5 diverse numerical columns if scoring columns aren't available
        cols = [c for c in df.select_dtypes(include='number').columns if df[c].nunique() > 1][:5]
    if not cols:
        return None

    sample = df[cols].head(max_recs)
    fig = px.parallel_coordinates(
        sample,
        color=cols[0],
        labels={c: c.replace("_", " ").title() for c in cols},
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig.update_layout(
        title="Recommendation Parallel Coordinates",
        title_font_size=20,
        margin=dict(l=40, r=40, t=75, b=40),
        font=dict(size=12),
    )
    return fig

def radar_for_listing(listing, averages):
    """
    Compare a listing's main stats against dataset averages using a radar chart.
    Returns None if not enough data is available.
    """
    stats = [
        ("avg_price", "Price"),
        ("avg_reviews", "Reviews"),
        ("avg_rating", "Rating"),
        ("avg_availability", "Availability"),
        ("avg_amenities", "Amenities"),
    ]
    listing_vals, avg_vals, labels = [], [], []
    for key, label in stats:
        val = listing.get(key)
        avg = averages.get(key)
        if val is None:
            # Try alternate naming in case column names differ
            val = listing.get(key.replace("avg_", ""))
        if isinstance(val, (int, float)) and isinstance(avg, (int, float)):
            listing_vals.append(val)
            avg_vals.append(avg)
            labels.append(label)
    if not listing_vals or not avg_vals:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=listing_vals,
        theta=labels,
        fill='toself',
        name='Listing'
    ))
    fig.add_trace(go.Scatterpolar(
        r=avg_vals,
        theta=labels,
        fill='toself',
        name='Average',
        line=dict(dash='dash')
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True,
        title="Listing vs. Average",
        title_font_size=18,
        margin=dict(t=65, l=30, r=30, b=30)
    )
    return fig
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def train_price_model(df):
    features = [c for c in ["latitude","longitude","number_of_reviews","availability_365"] if c in df.columns]
    if not features:
        raise ValueError("No feature columns available for price model.")
    df = df.dropna(subset=features + ["price"])
    X = df[features]
    y = df["price"]
    model = LinearRegression()
    model.fit(X, y)
    df["predicted_price"] = model.predict(X)
    return model, df

def cluster_hosts(df, n_clusters=4):
    features = [c for c in ["price","number_of_reviews","availability_365"] if c in df.columns]
    df = df.dropna(subset=features)
    if len(df) < n_clusters:
        n_clusters = max(2, len(df))
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[features])
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_scaled)
    return kmeans, df
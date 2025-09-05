ProphetBnB: Airbnb Price Prediction & Host Segmentation

<!-- Optional: replace with actual logo -->

ProphetBnB is a comprehensive Python project that predicts Airbnb listing prices and segments hosts using clustering. It provides interactive visualizations and a Streamlit web app for easy exploration of Airbnb listings.

Table of Contents

Features

Project Structure

Installation

Usage

Dataset

Dependencies

Contributing

License

Features

Price Prediction

Uses machine learning regression models to predict Airbnb listing prices.

Identifies underpriced and overpriced listings.

Host Clustering

Clusters hosts based on price, reviews, and availability.

Supports segmentation for marketing insights.

Interactive Visualizations

Folium maps for geographic distribution.

Plotly charts for interactive cluster and feature analysis.

Streamlit App

User-friendly interface for exploring predictions and visualizations.

Accessible locally or via web deployment.

Project Structure
AirBnB-PriceSense/
│
├── data/
│   ├── raw/               # Original datasets (CSV/JSON)
│   └── processed/         # Cleaned datasets ready for modeling
│
├── notebooks/
│   ├── 01_EDA.ipynb       # Exploratory Data Analysis
│   └── 02_Modeling.ipynb  # Regression & Clustering Models
│
├── src/
│   ├── data_preprocessing.py   # Data cleaning and feature engineering
│   ├── model_training.py       # Model training and evaluation
│   └── visualizations.py       # Plotting and map visualizations
│
├── app/
│   └── prophetbnb_app.py       # Streamlit interactive app
│
├── assets/
│   └── logo.png                # Optional: logo or images for README
│
├── environment.yml             # Conda environment configuration
├── requirements.txt            # Pip dependencies
└── README.md                   # Project overview and instructions

Installation
1. Using Conda (Recommended)
# Navigate to project folder
cd C:\Testing_New_Things\AirBnB-PriceSense

# Create environment
conda env create -f environment.yml

# Activate environment
conda activate ProphetBnB

2. Using Pip / Virtualenv
# Create virtual environment
python -m venv ProphetBnB_env

# Activate environment
ProphetBnB_env\Scripts\activate   # Windows
source ProphetBnB_env/bin/activate # macOS/Linux

# Install dependencies
pip install -r requirements.txt

Usage
1. Run Jupyter Notebooks
jupyter notebook


01_EDA.ipynb → Explore dataset, visualize distributions.

02_Modeling.ipynb → Train regression & clustering models.

2. Run Streamlit App
streamlit run app/prophetbnb_app.py


Explore predictions and visualizations interactively.

Supports local and web deployment.

Example Screenshot:

<!-- Replace with actual screenshot -->

Dataset

Place your Airbnb dataset in data/raw/listings.csv.

data_preprocessing.py generates a cleaned dataset in data/processed/listings_clean.csv.

Recommended Dataset Sources:

Inside Airbnb

Kaggle Airbnb Datasets

Dependencies

Python 3.11+

pandas, numpy, scikit-learn

matplotlib, seaborn, plotly

geopandas, folium, streamlit, streamlit-folium

joblib, pyyaml

Jupyter Notebook

All dependencies are listed in environment.yml and requirements.txt.

Contributing

Fork the repository and create a new branch.

Make your changes and test thoroughly.

Submit a pull request with a clear description.

License

This project is licensed under the MIT License. See the LICENSE
 file for details.
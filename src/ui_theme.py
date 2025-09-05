from __future__ import annotations
import streamlit as st
import base64

DEFAULT_CSS = """
/* Full page gradient background (fallback) */
.stApp {
  background: linear-gradient(135deg, #141e30 0%, #243b55 100%);
  background-attachment: fixed;
  color: #f2f4f8;
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Optional background image overlay (injected dynamically) */
body.custom-bg:before {
  content: "";
  position: fixed;
  inset: 0;
  background-size: cover;
  background-position: center;
  opacity: 0.28;
  z-index: -1;
}

/* Card-like sections */
.block-container {
  padding-top: 1rem;
}

section.main > div {
  backdrop-filter: blur(2px);
}

.sidebar .sidebar-content, .css-1d391kg, .css-1cypcdb {
  backdrop-filter: blur(4px);
}

h1, h2, h3, h4 {
  font-weight: 600;
  letter-spacing: .5px;
}

[data-testid="stSidebar"] {
  background: rgba(20, 31, 49, 0.85);
  border-right: 1px solid rgba(255,255,255,0.06);
}

.stMetric {
  background: rgba(255,255,255,0.07);
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.1);
}

div[data-baseweb="select"] > div {
  background: #1f2937;
}

.stDownloadButton button, .stButton button {
  border-radius: 8px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.stTabs [data-baseweb="tab-list"] {
  gap: .5rem;
}
.stTabs [data-baseweb="tab"] {
  background: rgba(255,255,255,0.07);
  border-radius: 8px;
  padding: 8px 14px;
  font-weight: 500;
}
.stTabs [aria-selected="true"] {
  background: #ff4b4b !important;
  color: #fff !important;
}

footer {visibility:hidden;}
"""

def inject_base_css():
    st.markdown(f"<style>{DEFAULT_CSS}</style>", unsafe_allow_html=True)

def set_background_image(file_bytes: bytes):
    """
    Inject a base64 image as low-opacity fixed background overlay.
    """
    b64 = base64.b64encode(file_bytes).decode()
    css = f"""
    <style>
    body.custom-bg:before {{
      background-image: url("data:image/png;base64,{b64}");
    }}
    </style>
    <script>
      document.body.classList.add('custom-bg');
    </script>
    """
    st.markdown(css, unsafe_allow_html=True)
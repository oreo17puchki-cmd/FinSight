import streamlit as st
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="FinSIGHT Real-Time Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom fonts from Google Fonts + Material Symbols (prevents icon names showing as raw text)
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@1,9..144,400;1,9..144,600;1,9..144,700&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Inter:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
    """,
    unsafe_allow_html=True
)


# FinSight — Pixel-Perfect Dark Sidebar & Light Cream Canvas Theme
st.markdown(
    """
    <style>
    /* ─── GLOBAL BASE & CANVAS BACKGROUND ─────────────────────────── */
    html, body,
    [data-testid="stAppViewContainer"],
    .stApp {
        background-color: #F3F4E3 !important; /* Soft light cream/beige tone */
        font-family: 'Inter', 'Plus Jakarta Sans', sans-serif !important;
        color: #1E293B !important;
    }

    /* Main content container */
    [data-testid="stAppViewBlockContainer"],
    div.block-container {
        background-color: #F3F4E3 !important;
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2.2rem !important; /* Clean spacious gap from sidebar */
        padding-right: 2.2rem !important;
    }
    header[data-testid="stHeader"] {
        height: 0px !important;
        background: transparent !important;
    }

    /* ─── 1. SIDEBAR CONTAINER & LAYOUT SPECS ─────────────────────── */
    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarUserContent"],
    [data-testid="stSidebar"] > div:first-child {
        background-color: #0E131F !important; /* Solid Deep Slate Navy */
        border: none !important;
        border-right: none !important;
        box-shadow: none !important;
    }

    [data-testid="stSidebar"] {
        min-width: 240px !important;
        max-width: 240px !important;
        width: 240px !important;
        height: 100vh !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }

    /* Inner wrapper for sidebar - reduced top padding to 1/3rd (8px 16px 24px 16px) */
    [data-testid="stSidebar"] > div:first-child {
        padding: 8px 16px 24px 16px !important;
        box-sizing: border-box !important;
        min-height: 100vh !important;
    }

    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        padding-top: 8px !important;
        margin-top: 0 !important;
    }

    /* Sidebar collapse / toggle button — hidden to prevent raw icon text from showing */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* ─── 2. BRANDING HEADER (TOP LEFT) ────────────────────────────── */
    .sidebar-brand-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 0 !important;
        margin-bottom: 24px;
        padding: 0 4px;
    }
    .sidebar-brand-title {
        font-size: 30px !important;
        line-height: 1.1 !important;
    }
    .brand-fin {
        font-family: 'Inter', 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
    }
    .brand-sight {
        font-family: 'Fraunces', 'Georgia', serif !important;
        font-style: italic !important;
        font-weight: 600 !important;
        color: #C9A56E !important; /* Elegant gold accent */
        margin-left: 1px !important;
    }
    .sidebar-brand-subtitle {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 9px !important;
        letter-spacing: 2.5px !important;
        text-transform: uppercase !important;
        color: #A0AEC0 !important;
        margin-top: 4px !important;
    }

    /* ─── 3 & 4. NAVIGATION BUTTON DIRECTIVES ─────────────────────── */
    [data-testid="stSidebar"] div.stButton {
        margin-bottom: 12px !important; /* Vertical margin 12px between items */
    }

    [data-testid="stSidebar"] div.stButton > button {
        background: transparent !important; /* Completely transparent */
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 16px 12px 44px !important; /* Horizontal padding 12px 16px + icon space */
        width: 100% !important;
        height: 44px !important;
        min-height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
        transition: all 0.18s ease !important;
        position: relative !important;
        background-repeat: no-repeat !important;
        background-position: 16px center !important;
        background-size: 18px 18px !important;
        box-sizing: border-box !important;
    }

    /* Target inner paragraph text inside Streamlit buttons explicitly */
    [data-testid="stSidebar"] div.stButton > button p,
    [data-testid="stSidebar"] div.stButton > button div[data-testid="stMarkdownContainer"] p {
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
        font-size: 14px !important;
        font-weight: 400 !important; /* Regular */
        color: #A0AEC0 !important; /* Muted Cool Gray */
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        transition: color 0.18s ease !important;
    }

    /* Hover State for Inactive Items */
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover p,
    [data-testid="stSidebar"] div.stButton > button:hover div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important; /* Transition to white */
    }

    /* SVG Background Icons for Inactive State (#A0AEC0 Outlined Icons) */
    div.st-key-nav_dashboard > button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23A0AEC0' stroke-width='2.2'%3E%3Crect x='3' y='3' width='7' height='7' rx='1.5'/%3E%3Crect x='14' y='3' width='7' height='7' rx='1.5'/%3E%3Crect x='14' y='14' width='7' height='7' rx='1.5'/%3E%3Crect x='3' y='14' width='7' height='7' rx='1.5'/%3E%3C/svg%3E") !important;
    }

    div.st-key-nav_income > button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23A0AEC0' stroke-width='2'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Cpolyline points='8 12 12 16 16 12'/%3E%3Cline x1='12' y1='8' x2='12' y2='16'/%3E%3C/svg%3E") !important;
    }
    div.st-key-nav_income > button:hover {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Cpolyline points='8 12 12 16 16 12'/%3E%3Cline x1='12' y1='8' x2='12' y2='16'/%3E%3C/svg%3E") !important;
    }

    div.st-key-nav_expenses > button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23A0AEC0' stroke-width='2'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Cpolyline points='16 12 12 8 8 12'/%3E%3Cline x1='12' y1='16' x2='12' y2='8'/%3E%3C/svg%3E") !important;
    }
    div.st-key-nav_expenses > button:hover {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Cpolyline points='16 12 12 8 8 12'/%3E%3Cline x1='12' y1='16' x2='12' y2='8'/%3E%3C/svg%3E") !important;
    }

    div.st-key-nav_budget > button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23A0AEC0' stroke-width='2'%3E%3Crect x='2' y='5' width='20' height='14' rx='2'/%3E%3Cpath d='M16 12h2'/%3E%3C/svg%3E") !important;
    }
    div.st-key-nav_budget > button:hover {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2'%3E%3Crect x='2' y='5' width='20' height='14' rx='2'/%3E%3Cpath d='M16 12h2'/%3E%3C/svg%3E") !important;
    }

    div.st-key-nav_goals > button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23A0AEC0' stroke-width='2'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Ccircle cx='12' cy='12' r='6'/%3E%3Ccircle cx='12' cy='12' r='2'/%3E%3C/svg%3E") !important;
    }
    div.st-key-nav_goals > button:hover {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Ccircle cx='12' cy='12' r='6'/%3E%3Ccircle cx='12' cy='12' r='2'/%3E%3C/svg%3E") !important;
    }

    div.st-key-nav_investments > button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23A0AEC0' stroke-width='2'%3E%3Cpolyline points='23 6 13.5 15.5 8.5 10.5 1 18'/%3E%3Cpolyline points='17 6 23 6 23 12'/%3E%3C/svg%3E") !important;
    }
    div.st-key-nav_investments > button:hover {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2'%3E%3Cpolyline points='23 6 13.5 15.5 8.5 10.5 1 18'/%3E%3Cpolyline points='17 6 23 6 23 12'/%3E%3C/svg%3E") !important;
    }

    div.st-key-nav_transactions > button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23A0AEC0' stroke-width='2'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3Cline x1='7' y1='8' x2='17' y2='8'/%3E%3Cline x1='7' y1='12' x2='17' y2='12'/%3E%3Cline x1='7' y1='16' x2='13' y2='16'/%3E%3C/svg%3E") !important;
    }
    div.st-key-nav_transactions > button:hover {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3Cline x1='7' y1='8' x2='17' y2='8'/%3E%3Cline x1='7' y1='12' x2='17' y2='12'/%3E%3Cline x1='7' y1='16' x2='13' y2='16'/%3E%3C/svg%3E") !important;
    }

    div.st-key-nav_reports > button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23A0AEC0' stroke-width='2'%3E%3Cline x1='18' y1='20' x2='18' y2='10'/%3E%3Cline x1='12' y1='20' x2='12' y2='4'/%3E%3Cline x1='6' y1='20' x2='6' y2='14'/%3E%3C/svg%3E") !important;
    }
    div.st-key-nav_reports > button:hover {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2'%3E%3Cline x1='18' y1='20' x2='18' y2='10'/%3E%3Cline x1='12' y1='20' x2='12' y2='4'/%3E%3Cline x1='6' y1='20' x2='6' y2='14'/%3E%3C/svg%3E") !important;
    }

    div.st-key-nav_settings > button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23A0AEC0' stroke-width='2'%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'/%3E%3C/svg%3E") !important;
    }
    div.st-key-nav_settings > button:hover {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2'%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'/%3E%3C/svg%3E") !important;
    }

    /* Sidebar Export Data Button */
    [data-testid="stSidebar"] .stDownloadButton > button {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #A0AEC0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] .stDownloadButton > button:hover {
        background-color: rgba(255, 255, 255, 0.12) !important;
        color: #FFFFFF !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    /* ─── FORCE WHITE BACKGROUND & BLACK BORDER ON ALL BUTTONS ─── */
    .stApp button,
    .stApp button[kind="primary"],
    .stApp button[kind="secondary"],
    .stApp button[data-testid="stBaseButton-primary"],
    .stApp button[data-testid="stBaseButton-secondary"],
    .stApp div[data-testid="stFormSubmitButton"] button,
    div[role="dialog"] button,
    div[data-testid="stDialog"] button {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease !important;
    }

    .stApp button *,
    .stApp button p,
    .stApp button span,
    .stApp button div,
    .stApp div[data-testid="stFormSubmitButton"] button *,
    div[role="dialog"] button * {
        color: #000000 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }

    .stApp button:hover,
    .stApp button[kind="primary"]:hover,
    .stApp button[kind="secondary"]:hover,
    .stApp div[data-testid="stFormSubmitButton"] button:hover,
    div[role="dialog"] button:hover {
        background-color: #F8FAFC !important;
        background: #F8FAFC !important;
        border-color: #000000 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12) !important;
        transform: translateY(-1px) !important;
    }

    /* ─── FORCE PURE WHITE THEME ON ALL DROPDOWNS & SELECTBOX POPOVERS ─── */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] *,
    ul[role="listbox"],
    ul[role="listbox"] *,
    li[role="option"],
    li[role="option"] *,
    div[role="option"],
    div[role="option"] * {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #000000 !important;
    }

    li[role="option"]:hover,
    li[role="option"]:hover *,
    li[role="option"][aria-selected="true"],
    li[role="option"][aria-selected="true"] *,
    div[role="option"]:hover,
    div[role="option"]:hover *,
    div[role="option"][aria-selected="true"],
    div[role="option"][aria-selected="true"] * {
        background-color: #F1F5F9 !important;
        background: #F1F5F9 !important;
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* ─── REMOVE ALL HEAVY BLACK BORDERS FROM ALL INPUT WIDGETS & CONTAINERS ─── */
    div[data-baseweb="base-input"],
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-testid="stTextInput"] > div,
    div[data-testid="stTextInput"] > div > div,
    div[data-testid="stNumberInput"] > div,
    div[data-testid="stNumberInput"] > div > div,
    div[data-testid="stNumberInputContainer"],
    div[data-testid="stSelectbox"] > div,
    div[data-testid="stSelectbox"] > div > div,
    div[data-testid="stDateInput"] > div,
    div[data-testid="stDateInput"] > div > div,
    div[data-testid="stTextArea"] > div,
    div[data-testid="stTextArea"] > div > div,
    div[data-baseweb="textarea"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-color: #CBD5E1 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* ─── FORCE BOLD BLACK TEXT ON ALL SELECTBOX VALUE TRIGGERS & INPUTS ─── */
    div[data-baseweb="select"] *,
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] p,
    div[data-baseweb="select"] input,
    div[data-testid="stSelectbox"] *,
    div[data-testid="stSelectbox"] div,
    div[data-testid="stSelectbox"] span,
    div[data-testid="stSelectbox"] p,
    div[data-baseweb="input"] input,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stTextArea"] textarea {
        color: #000000 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }

    /* Inner input text & textareas */
    div[data-baseweb="input"] input,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* ─── GREYED OUT PLACEHOLDER TEXT ─── */
    div[data-baseweb="input"] input::placeholder,
    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stNumberInput"] input::placeholder,
    div[data-testid="stDateInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #9CA3AF !important;
        -webkit-text-fill-color: #9CA3AF !important;
        font-weight: 400 !important;
        opacity: 1 !important;
    }

    /* Selectbox Arrow Dropdown Buttons & Number Input Step Controls */
    div[data-baseweb="select"] button,
    div[data-baseweb="select"] svg,
    div[data-baseweb="select"] div:last-child,
    div[data-testid="stNumberInputStepDown"],
    div[data-testid="stNumberInputStepUp"],
    div[data-testid="stNumberInputContainer"] button {
        background-color: transparent !important;
        border: none !important;
        border-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
        color: #475569 !important;
    }



    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    div[data-testid="stTextInput"] > div:focus-within,
    div[data-testid="stNumberInput"] > div:focus-within,
    div[data-testid="stTextArea"] > div:focus-within {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15) !important;
    }

    /* ─── DATE PICKER CALENDAR POPOVER — WHITE THEME & NO BLACK BOXES ─── */
    div[data-baseweb="calendar"],
    div[data-baseweb="calendar"] *,
    div[data-baseweb="calendar"] div,
    div[data-baseweb="calendar"] header,
    div[data-baseweb="calendar"] button,
    div[data-baseweb="calendar"] [role="gridcell"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #000000 !important;
    }

    /* Disabled / Empty Calendar Days (Eliminates Pitch Black Boxes) */
    div[data-baseweb="calendar"] [aria-disabled="true"],
    div[data-baseweb="calendar"] [aria-disabled="true"] * {
        background-color: #F8FAFC !important;
        background: #F8FAFC !important;
        color: #CBD5E1 !important;
        border: none !important;
    }

    /* Selected Date Item */
    div[data-baseweb="calendar"] [aria-selected="true"],
    div[data-baseweb="calendar"] [aria-selected="true"] * {
        background-color: #EF4444 !important;
        background: #EF4444 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Calendar Day Hover state */
    div[data-baseweb="calendar"] [role="gridcell"]:hover:not([aria-disabled="true"]) {
        background-color: #F1F5F9 !important;
        background: #F1F5F9 !important;
        color: #000000 !important;
    }

    /* ─── POPUP DIALOG MODAL CLOSE BUTTON (TOP RIGHT CROSS ICON) ───── */
    div[role="dialog"] button[aria-label="Close"],
    div[data-testid="stDialog"] button[aria-label="Close"],
    div[data-testid="stModal"] button[aria-label="Close"],
    div[role="dialog"] header button,
    div[data-testid="stDialog"] header button {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        min-height: 32px !important;
        max-height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        opacity: 1 !important;
        visibility: visible !important;
        top: 16px !important;
        right: 16px !important;
        position: absolute !important;
        cursor: pointer !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.15s ease !important;
    }

    div[role="dialog"] button[aria-label="Close"] svg,
    div[data-testid="stDialog"] button[aria-label="Close"] svg,
    div[role="dialog"] header button svg,
    div[data-testid="stDialog"] header button svg {
        stroke: #0F172A !important;
        color: #0F172A !important;
        fill: #0F172A !important;
        width: 16px !important;
        height: 16px !important;
        stroke-width: 2.5 !important;
    }

    div[role="dialog"] button[aria-label="Close"]:hover,
    div[data-testid="stDialog"] button[aria-label="Close"]:hover,
    div[role="dialog"] header button:hover,
    div[data-testid="stDialog"] header button:hover {
        background-color: #E2E8F0 !important;
        color: #000000 !important;
        transform: scale(1.05) !important;
    }

    .stApp div[class*="st-key-edit_"] > button,
    .stApp div[class*="st-key-edit_"] button,
    .stApp div[class*="st-key-edit_"] button[data-testid="stBaseButton-secondary"],
    .stApp div[class*="st-key-delete_"] > button,
    .stApp div[class*="st-key-delete_"] button,
    .stApp div[class*="st-key-delete_"] button[data-testid="stBaseButton-secondary"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1.5px solid #000000 !important;
        border-radius: 6px !important;
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 8px !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
    }
    .stApp div[class*="st-key-edit_"] button *,
    .stApp div[class*="st-key-edit_"] button p,
    .stApp div[class*="st-key-edit_"] button span,
    .stApp div[class*="st-key-delete_"] button *,
    .stApp div[class*="st-key-delete_"] button p,
    .stApp div[class*="st-key-delete_"] button span {
        color: #000000 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 12px !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }

    .stApp div.st-key-btn_add_expense_main button:hover,
    .stApp div.st-key-btn_save_expense_modal button:hover,
    .stApp div[class*="st-key-edit_"] button:hover,
    .stApp div[class*="st-key-delete_"] button:hover {
        background-color: #F8FAFC !important;
        background: #F8FAFC !important;
        border-color: #000000 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12) !important;
        transform: translateY(-1px) !important;
    }

    /* ─── MAIN PAGE HEADER ─────────────────────────────────────── */
    .main-page-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    .main-page-title {
        font-family: 'Inter', 'Plus Jakarta Sans', sans-serif;
        font-size: 24px;
        font-weight: 800;
        color: #1A202C;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .main-page-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        color: #718096;
        margin-top: 4px;
        font-weight: 400;
    }
    .header-controls {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .dark-circle-btn {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: #1A202C;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .light-circle-btn {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }

    /* ─── IMAGE 3 KPI CARDS ─────────────────────────────────────── */
    .kpi-card {
        background-color: #FFFFFF !important;
        border-radius: 18px !important;
        padding: 22px 24px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(226, 232, 240, 0.7) !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        transition: box-shadow 0.2s ease, transform 0.2s ease !important;
    }
    .kpi-card:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.07) !important;
        transform: translateY(-2px) !important;
    }

    /* ─── VISUALIZATION SECTION CARDS (PIE CHART & LINE CHART ONLY) ─── */
    .viz-section [data-testid="stColumn"] {
        background-color: #FFFFFF !important;
        border-radius: 18px !important;
        padding: 22px 24px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(226, 232, 240, 0.7) !important;
        box-sizing: border-box !important;
        transition: box-shadow 0.2s ease, transform 0.2s ease !important;
    }
    .viz-section [data-testid="stColumn"]:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.07) !important;
        transform: translateY(-2px) !important;
    }

    /* Exclude mode buttons sub-columns inside viz-section */
    .viz-section [data-testid="stColumn"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        background-color: transparent !important;
        border-radius: 0 !important;
        padding: 0 !important;
        box-shadow: none !important;
        border: none !important;
        transform: none !important;
    }

    .kpi-title {
        font-family: 'Inter', sans-serif !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.6px !important;
        text-transform: uppercase !important;
        margin-bottom: 10px !important;
    }
    .kpi-value {
        font-family: 'Inter', 'Plus Jakarta Sans', sans-serif !important;
        font-size: 23px !important;
        font-weight: 800 !important;
        color: #1A202C !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 8px !important;
    }
    .kpi-subtext {
        font-family: 'Inter', sans-serif !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        color: #718096 !important;
    }

    /* ─── SECTION / CHART CARDS ───────────────────────────────── */
    .section-card {
        background-color: #FFFFFF !important;
        border-radius: 18px !important;
        padding: 24px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(226, 232, 240, 0.7) !important;
        margin-bottom: 20px;
    }
    .section-title {
        font-family: 'Inter', 'Plus Jakarta Sans', sans-serif !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        color: #1A202C !important;
        margin-bottom: 16px !important;
    }

    /* ─── INPUT FIELDS ────────────────────────────────────────── */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: #F8FAFC !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        color: #1E293B !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 14px !important;
        transition: border-color 0.2s ease !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #16A34A !important;
        box-shadow: 0 0 0 3px rgba(22,163,74,0.15) !important;
    }

    /* Selectbox Container & Selected Text - Pure White Block with Bold Black Text */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stSelectbox"] div[data-baseweb="select"],
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #000000 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
    }
    [data-testid="stSelectbox"] div[data-baseweb="select"] *,
    [data-testid="stSelectbox"] div[data-baseweb="select"] span,
    [data-testid="stSelectbox"] div[data-baseweb="select"] div,
    [data-testid="stSelectbox"] div[data-baseweb="select"] p,
    [data-testid="stSelectbox"] div[data-baseweb="select"] svg {
        color: #000000 !important;
        fill: #000000 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        opacity: 1 !important;
    }
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] * {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }

    /* ─── LABELS ──────────────────────────────────────────────── */
    label {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        color: #64748B !important;
        letter-spacing: 0.04em !important;
    }

    /* ─── BUTTONS & DIALOGS ──────────────────────────────────── */
    div.stFormSubmitButton > button,
    div.stButton > button.add-btn {
        background-color: #16A34A !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 12px rgba(22,163,74,0.3) !important;
        transition: all 0.2s ease !important;
    }
    div.stFormSubmitButton > button:hover {
        background-color: #15803D !important;
        box-shadow: 0 6px 18px rgba(22,163,74,0.4) !important;
    }

    /* Modal / Dialog */
    [data-testid="stDialog"] > div,
    div[role="dialog"] {
        background-color: #FFFFFF !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 20px 60px rgba(0,0,0,0.15) !important;
    }

    /* ─── SCROLLBAR ───────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #F3F4E3; }
    ::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Mocking or getting current user session state
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = 1
    st.session_state['username'] = "Venkat"
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "Dashboard"

uid = st.session_state['user_id']
uname = st.session_state['username']

# Database connection
def get_db_conn():
    return psycopg2.connect(os.environ.get("SUPABASE_DB_URI"))

# Insert transaction function
def add_transaction(user_id, amount, t_type, category, date, description, payment_mode=None):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO transactions (user_id, amount, type, category, date, description, payment_mode) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, amount, t_type, category, date, description, payment_mode)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Error saving transaction: {e}")
    finally:
        cur.close()
        conn.close()

# Real-time queries
conn = get_db_conn()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 2. Monthly Income — fixed at ₹60,000 per month
monthly_income = 60000.0

# 3. Monthly Expenses — filtered to active calendar month (auto-resets to ₹0 on 1st of each month)
cur.execute(
    """
    SELECT COALESCE(SUM(amount), 0) as monthly_expenses 
    FROM transactions 
    WHERE user_id = %s
      AND type = 'Expense'
      AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
      AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
    """,
    (uid,)
)
monthly_expenses = float(cur.fetchone()['monthly_expenses'])

total_balance = monthly_income - monthly_expenses

# Month-over-month delta for Total Balance
cur.execute(
    """
    SELECT 
        COALESCE(SUM(CASE WHEN type='Income' THEN amount ELSE -amount END), 0) as last_month_balance 
    FROM transactions 
    WHERE user_id = %s 
      AND date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
      AND date < DATE_TRUNC('month', CURRENT_DATE)
    """,
    (uid,)
)
last_month_bal = float(cur.fetchone()['last_month_balance'])
if last_month_bal == 0:
    balance_delta_str = "↑ 0% from last month"
else:
    delta_pct = ((total_balance - last_month_bal) / abs(last_month_bal)) * 100
    balance_delta_str = f"{'↑' if delta_pct >= 0 else '↓'} {abs(delta_pct):.1f}% from last month"

# Calculations based on overridden Income - Expenses finished above

# 4. Savings Rate
if monthly_income > 0:
    savings_rate = ((monthly_income - monthly_expenses) / monthly_income) * 100
else:
    savings_rate = 0.0

# Query transactions grouped by category (for donut chart) - restricted to current month/year
cur.execute(
    """
    SELECT category, SUM(amount) as total 
    FROM transactions 
    WHERE user_id = %s AND type = 'Expense' 
      AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE) 
      AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
    GROUP BY category
    """,
    (uid,)
)
category_data = cur.fetchall()
df_category = pd.DataFrame(category_data) if category_data else pd.DataFrame(columns=['category', 'total'])
if not df_category.empty:
    df_category['total'] = df_category['total'].astype(float)

# Query transactions by date (for side-by-side grouped bar chart) - restricted to last 30 days
cur.execute(
    """
    SELECT 
        DATE(date) as tx_date,
        SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) as income,
        SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as expense
    FROM transactions
    WHERE user_id = %s 
      AND date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY DATE(date)
    ORDER BY tx_date ASC
    """,
    (uid,)
)
monthly_overview_data = cur.fetchall()
df_monthly = pd.DataFrame(monthly_overview_data) if monthly_overview_data else pd.DataFrame(columns=['tx_date', 'income', 'expense'])
if not df_monthly.empty:
    df_monthly['income'] = df_monthly['income'].astype(float)
    df_monthly['expense'] = df_monthly['expense'].astype(float)
    # Format date label as "MMM DD" (e.g. Jun 25)
    df_monthly['formatted_date'] = pd.to_datetime(df_monthly['tx_date']).dt.strftime('%b %d')

# Fetch all transactions for CSV download
cur.execute(
    "SELECT date, type, category, amount, description FROM transactions WHERE user_id = %s ORDER BY date DESC",
    (uid,)
)
all_transactions = cur.fetchall()
df_all = pd.DataFrame(all_transactions) if all_transactions else pd.DataFrame(columns=['date', 'type', 'category', 'amount', 'description'])

cur.close()
conn.close()


# --- SIDEBAR NAVIGATION (DARK THEME) ---
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand-container">
            <div>
                <div class="sidebar-brand-title">
                    <span class="brand-fin">Fin</span><span class="brand-sight">Sight</span>
                </div>
                <div class="sidebar-brand-subtitle">BUDGET & WEALTH</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Navigation Items matching Image 2
    nav_items = [
        ("Dashboard", "Dashboard", "nav_dashboard"),
        ("Income", "Income", "nav_income"),
        ("Expenses", "Expenses", "nav_expenses"),
        ("Budget", "Budget", "nav_budget"),
        ("Goals", "Goals", "nav_goals"),
        ("Investments", "Investments", "nav_investments"),
        ("Transactions", "Transactions", "nav_transactions"),
        ("Reports", "Reports", "nav_reports"),
        ("Settings", "Settings", "nav_settings"),
    ]
    
    for tab_name, label, key_name in nav_items:
        if st.button(label, key=key_name, use_container_width=True):
            st.session_state['active_tab'] = tab_name
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CSV Export Button
    if not df_all.empty:
        csv_data = df_all.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Data",
            data=csv_data,
            file_name="transactions.csv",
            mime="text/csv",
            use_container_width=True,
            key="export_btn"
        )
    else:
        st.button("Export Data", disabled=True, use_container_width=True, key="export_btn_disabled")

# Dynamically apply Emerald Green active pill styling to current active tab button
active_tab = st.session_state.get('active_tab', 'Dashboard')
active_key = f"nav_{active_tab.lower()}"

st.markdown(
    f"""
    <style>
    div.st-key-{active_key} > button {{
        background-color: #16A34A !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 14px rgba(22, 163, 74, 0.35) !important;
    }}
    div.st-key-{active_key} > button p,
    div.st-key-{active_key} > button div[data-testid="stMarkdownContainer"] p {{
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}
    div.st-key-{active_key} > button:hover {{
        background-color: #15803D !important;
    }}
    div.st-key-nav_{active_tab.lower()} > button {{
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2.2'%3E%3Crect x='3' y='3' width='7' height='7' rx='1.5'/%3E%3Crect x='14' y='3' width='7' height='7' rx='1.5'/%3E%3Crect x='14' y='14' width='7' height='7' rx='1.5'/%3E%3Crect x='3' y='14' width='7' height='7' rx='1.5'/%3E%3C/svg%3E") !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Analytics & Expense Reduction Insights Dialog
@st.dialog("Financial Analytics & Savings Insights")
def show_analytics_dialog():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT category, SUM(amount) as total 
        FROM transactions 
        WHERE user_id = %s AND type = 'Expense' AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE) AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
        GROUP BY category
        ORDER BY total DESC
        """,
        (uid,)
    )
    cat_rows = cur.fetchall()
    
    # Query for expenses > 5000
    cur.execute(
        """
        SELECT TO_CHAR(date, 'Mon DD') as short_date, category, description, amount
        FROM transactions
        WHERE user_id = %s 
          AND type = 'Expense' 
          AND amount > 5000 
          AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE) 
          AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
        ORDER BY date DESC
        """,
        (uid,)
    )
    high_expenses = cur.fetchall()
    
    cur.close()
    conn.close()
    
    if not cat_rows:
        st.info("No expense transactions recorded for the current month yet. Add expenses to generate insights.")
        return
        
    tot_exp = sum(float(r['total']) for r in cat_rows)
    top_cat = cat_rows[0]
    top_cat_name = str(top_cat['category'])
    top_cat_amt = float(top_cat['total'])
    top_cat_pct = (top_cat_amt / tot_exp * 100.0) if tot_exp > 0 else 0.0

    # Advisory rules for discretionary categories
    discretionary_map = {
        'Dining': (0.30, "Cook at home 2 more days per week and reduce delivery orders."),
        'Shopping': (0.25, "Apply a 48-hour delay rule before non-essential purchases."),
        'Entertainment': (0.35, "Audit active streaming subscriptions and leisure outings."),
        'Travel': (0.20, "Opt for carpooling or public transport for routine commutes."),
        'Other': (0.25, "Track daily micro-transactions and impulse cash / UPI spending.")
    }

    reduction_suggestions = []
    potential_savings_total = 0.0

    for r in cat_rows:
        c_name = str(r['category'])
        c_amt = float(r['total'])
        if c_name in discretionary_map:
            save_rate, tip = discretionary_map[c_name]
            possible_savings = c_amt * save_rate
            potential_savings_total += possible_savings
            reduction_suggestions.append({
                'category': c_name,
                'amount': c_amt,
                'pct': (c_amt / tot_exp * 100.0) if tot_exp > 0 else 0.0,
                'potential_savings': possible_savings,
                'tip': tip
            })

    # Render Dialog Content
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(
            f"""
            <div style="background: #FFF5F5; padding: 12px; border-radius: 10px; border: 1px solid #FEB2B2; text-align: center;">
                <div style="font-size: 11px; font-weight: 700; color: #9B2C2C; text-transform: uppercase;">Highest Category</div>
                <div style="font-size: 16px; font-weight: 800; color: #E53E3E; margin: 4px 0;">{top_cat_name}</div>
                <div style="font-size: 12px; font-weight: 600; color: #742A2A;">₹{top_cat_amt:,.2f} ({top_cat_pct:.1f}%)</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m_col2:
        st.markdown(
            f"""
            <div style="background: #F0FDF4; padding: 12px; border-radius: 10px; border: 1px solid #BBF7D0; text-align: center;">
                <div style="font-size: 11px; font-weight: 700; color: #166534; text-transform: uppercase;">Est. Savings Target</div>
                <div style="font-size: 16px; font-weight: 800; color: #16A34A; margin: 4px 0;">₹{potential_savings_total:,.2f}</div>
                <div style="font-size: 12px; font-weight: 600; color: #14532D;">Per Month Potential</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m_col3:
        exp_ratio = (tot_exp / monthly_income * 100.0) if monthly_income > 0 else 0.0
        st.markdown(
            f"""
            <div style="background: #F8FAFC; padding: 12px; border-radius: 10px; border: 1px solid #E2E8F0; text-align: center;">
                <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;">Expense Ratio</div>
                <div style="font-size: 16px; font-weight: 800; color: {'#DC2626' if exp_ratio > 50 else '#2563EB'}; margin: 4px 0;">{exp_ratio:.1f}%</div>
                <div style="font-size: 12px; font-weight: 600; color: #334155;">Of Monthly Income</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<hr style='margin: 16px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 12px;'>Where You Can Reduce Expenses</h4>", unsafe_allow_html=True)

    if reduction_suggestions:
        for sug in reduction_suggestions:
            st.markdown(
                f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 700; font-size: 14px; color: #1E293B;">{sug['category']}</span>
                        <span style="font-weight: 700; font-size: 13px; color: #16A34A; background: #F0FDF4; padding: 2px 8px; border-radius: 6px; border: 1px solid #BBF7D0;">Save ~₹{sug['potential_savings']:,.2f}/mo</span>
                    </div>
                    <div style="font-size: 13px; color: #475569;">
                        Currently spending <b>₹{sug['amount']:,.2f}</b> ({sug['pct']:.1f}% of total expenses).
                    </div>
                    <div style="font-size: 12px; color: #334155; margin-top: 6px; font-style: italic; background: #F8FAFC; padding: 6px 8px; border-radius: 6px;">
                        <b>Recommendation:</b> {sug['tip']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            f"""
            <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 14px; color: #166534; font-size: 13.5px;">
                <b>Healthy Spending!</b> Your expenses are focused on essential categories (e.g. <b>{top_cat_name}</b>). Maintain your budget discipline.
            </div>
            """,
            unsafe_allow_html=True
        )

    if high_expenses:
        st.markdown("<hr style='margin: 16px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 12px;'>Expenses More than 5000</h4>", unsafe_allow_html=True)
        for hexp in high_expenses:
            st.markdown(
                f"""
                <div style="background-color: #FFF5F5; border: 1px solid #FEB2B2; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 700; font-size: 14px; color: #9B2C2C;">{hexp['description']}</span>
                        <span style="font-weight: 700; font-size: 13px; color: #C53030;">₹{float(hexp['amount']):,.2f}</span>
                    </div>
                    <div style="font-size: 13px; color: #742A2A;">
                        {hexp['category']} • {hexp['short_date']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

today_str = datetime.now().strftime('%A, %B %d, %Y')
current_month_name = datetime.now().strftime('%B')

head_col1, head_col2 = st.columns([3.2, 1])
with head_col1:
    st.markdown(
        f"""
        <div class="main-page-header">
            <div class="main-page-header-left">
                <div class="main-page-title">
                    Income and Expense Tracker
                </div>
                <div class="main-page-subtitle">
                    Take control of your finances <span style="margin: 0 6px; color: #CBD5E1;">|</span> Today is {today_str}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
with head_col2:
    if st.button("View Analytics", key="btn_view_analytics_header", use_container_width=True):
        show_analytics_dialog()

# 4 KPI Cards matching Image 3
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #718096;">TOTAL BALANCE</div>
            <div class="kpi-value">₹{total_balance:,.2f}</div>
            <div class="kpi-subtext" style="color: #279655; font-weight: 600;">↑ 0% from last month</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #3182CE;">MONTHLY INCOME</div>
            <div class="kpi-value">₹{monthly_income:,.2f}</div>
            <div class="kpi-subtext">📅 {current_month_name}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #E53E3E;">MONTHLY EXPENSES</div>
            <div class="kpi-value">₹{monthly_expenses:,.2f}</div>
            <div class="kpi-subtext">📅 {current_month_name}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    total_savings = max(0.0, monthly_income - monthly_expenses)
    savings_rate = (total_savings / monthly_income * 100.0) if monthly_income > 0 else 0.0
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #718096;">SAVINGS RATE</div>
            <div class="kpi-value" style="color: #279655;">{savings_rate:.1f}%</div>
            <div class="kpi-subtext">% Of income</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")

# Visualizations Grid
st.markdown('<div class="viz-section">', unsafe_allow_html=True)
viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    st.markdown('<div class="section-title">Spending by Category</div>', unsafe_allow_html=True)
    if not df_category.empty:
        # Fixed distinct vivid colors per expense category — never randomized
        color_map = {
            'Dining':          '#EF4444',   # Red
            'Groceries':       '#22C55E',   # Green
            'Entertainment':   '#A855F7',   # Purple
            'Home Essentials': '#3B82F6',   # Blue
            'Shopping':        '#F97316',   # Orange
            'Travel':          '#EAB308',   # Yellow
            'Other':           '#64748B'    # Slate grey
        }
        fig_donut = px.pie(
            df_category,
            values='total',
            names='category',
            hole=0.55,
            color='category',
            color_discrete_map=color_map,
            labels={'total': 'Total Spent', 'category': 'Category'}
        )
        fig_donut.update_traces(
            textinfo='percent',
            hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.2f}<br>Share: %{percent}"
        )
        fig_donut.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#334155',
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
                font=dict(size=12, color='#334155')
            )
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        
        # Detailed Category Breakdown List below Pie Chart
        total_category_expense = float(df_category['total'].sum()) if not df_category.empty else 0.0
        
        st.markdown('<hr style="margin: 16px 0 12px 0; border-top: 1px solid #E2E8F0;">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight: 700; font-size: 14px; color: #1E293B; margin-bottom: 10px;">Category Breakdown</div>', unsafe_allow_html=True)
        
        df_cat_sorted = df_category.sort_values(by='total', ascending=False)
        for _, row in df_cat_sorted.iterrows():
            cat_name = str(row['category'])
            amt = float(row['total'])
            share_pct = (amt / total_category_expense * 100.0) if total_category_expense > 0 else 0.0
            dot_color = color_map.get(cat_name, '#64748B')
            
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; margin-bottom: 6px; background-color: #F8FAFC; border-radius: 8px; border: 1px solid #F1F5F9;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: {dot_color};"></span>
                        <span style="font-weight: 600; font-size: 13.5px; color: #1E293B;">{cat_name}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-weight: 700; font-size: 14px; color: #0F172A;">₹{amt:,.2f}</span>
                        <span style="font-size: 12px; font-weight: 700; color: #475569; background: #FFFFFF; padding: 2px 8px; border-radius: 6px; border: 1px solid #E2E8F0;">{share_pct:.1f}%</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No expense transactions recorded yet.")

with viz_col2:
    header_c1, header_c2 = st.columns([1.2, 1])
    with header_c1:
        st.markdown('<div class="section-title">Expense Trend</div>', unsafe_allow_html=True)
    with header_c2:
        current_mode = st.session_state.get('expense_window', 'Monthly')
        
        monthly_border = "2.5px solid #000000" if current_mode == "Monthly" else "1px solid #CBD5E1"
        monthly_color = "#000000" if current_mode == "Monthly" else "#64748B"
        monthly_weight = "700" if current_mode == "Monthly" else "500"
        monthly_shadow = "0 2px 8px rgba(0, 0, 0, 0.12)" if current_mode == "Monthly" else "none"

        weekly_border = "2.5px solid #000000" if current_mode == "Weekly" else "1px solid #CBD5E1"
        weekly_color = "#000000" if current_mode == "Weekly" else "#64748B"
        weekly_weight = "700" if current_mode == "Weekly" else "500"
        weekly_shadow = "0 2px 8px rgba(0, 0, 0, 0.12)" if current_mode == "Weekly" else "none"

        # Ultra-high specificity CSS for white toggle buttons with black border lining
        st.markdown(
            f"""
            <style>
            .stApp div.st-key-btn_mode_monthly > button,
            .stApp div.st-key-btn_mode_monthly button,
            .stApp div.st-key-btn_mode_monthly button[data-testid="stBaseButton-secondary"],
            .stApp div.st-key-btn_mode_monthly button:hover,
            .stApp div.st-key-btn_mode_monthly button:focus,
            .stApp div.st-key-btn_mode_monthly button:active {{
                background-color: #FFFFFF !important;
                background: #FFFFFF !important;
                border: {monthly_border} !important;
                border-radius: 10px !important;
                height: 38px !important;
                min-height: 38px !important;
                padding: 0 !important;
                box-shadow: {monthly_shadow} !important;
            }}
            .stApp div.st-key-btn_mode_monthly button *,
            .stApp div.st-key-btn_mode_monthly button p,
            .stApp div.st-key-btn_mode_monthly button div,
            .stApp div.st-key-btn_mode_monthly button span {{
                color: {monthly_color} !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: {monthly_weight} !important;
                font-size: 13.5px !important;
                margin: 0 !important;
            }}
            .stApp div.st-key-btn_mode_weekly > button,
            .stApp div.st-key-btn_mode_weekly button,
            .stApp div.st-key-btn_mode_weekly button[data-testid="stBaseButton-secondary"],
            .stApp div.st-key-btn_mode_weekly button:hover,
            .stApp div.st-key-btn_mode_weekly button:focus,
            .stApp div.st-key-btn_mode_weekly button:active {{
                background-color: #FFFFFF !important;
                background: #FFFFFF !important;
                border: {weekly_border} !important;
                border-radius: 10px !important;
                height: 38px !important;
                min-height: 38px !important;
                padding: 0 !important;
                box-shadow: {weekly_shadow} !important;
            }}
            .stApp div.st-key-btn_mode_weekly button *,
            .stApp div.st-key-btn_mode_weekly button p,
            .stApp div.st-key-btn_mode_weekly button div,
            .stApp div.st-key-btn_mode_weekly button span {{
                color: {weekly_color} !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: {weekly_weight} !important;
                font-size: 13.5px !important;
                margin: 0 !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        mode_c1, mode_c2 = st.columns(2)
        with mode_c1:
            if st.button("Monthly", key="btn_mode_monthly", use_container_width=True):
                st.session_state['expense_window'] = "Monthly"
                st.rerun()
        with mode_c2:
            if st.button("Weekly", key="btn_mode_weekly", use_container_width=True):
                st.session_state['expense_window'] = "Weekly"
                st.rerun()
                
    expense_window = st.session_state.get('expense_window', 'Monthly')
    
    # Query MySQL in real time based on active View Mode selection
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    if expense_window == "Weekly":
        # Mode A: Weekly (Current active calendar week, excluding expenses > 5000)
        cur.execute(
            """
            SELECT 
                TRIM(TO_CHAR(date, 'Day')) as day_name,
                COALESCE(SUM(amount), 0) as total_expense
            FROM transactions
            WHERE user_id = %s 
              AND type = 'Expense' 
              AND amount <= 5000
              AND YEARWEEK(date, 1) = YEARWEEK(CURRENT_DATE, 1)
            GROUP BY TRIM(TO_CHAR(date, 'Day'))
            """,
            (uid,)
        )
        weekly_rows = cur.fetchall()
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        short_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        weekly_map = {r['day_name']: float(r['total_expense']) for r in weekly_rows} if weekly_rows else {}
        
        x_vals = short_days
        y_vals = [weekly_map.get(day, 0.0) for day in days_order]
    else:
        # Mode B: Monthly (Week 1 to Week 4 buckets of current month, excluding expenses > 5000)
        cur.execute(
            """
            SELECT 
                CASE 
                    WHEN EXTRACT(DAY FROM date) BETWEEN 1 AND 7 THEN 'Week 1'
                    WHEN EXTRACT(DAY FROM date) BETWEEN 8 AND 14 THEN 'Week 2'
                    WHEN EXTRACT(DAY FROM date) BETWEEN 15 AND 21 THEN 'Week 3'
                    ELSE 'Week 4'
                END as week_bucket,
                COALESCE(SUM(amount), 0) as total_expense
            FROM transactions
            WHERE user_id = %s 
              AND type = 'Expense'
              AND amount <= 5000
              AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE) 
              AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
            GROUP BY week_bucket
            ORDER BY week_bucket ASC
            """,
            (uid,)
        )
        monthly_rows = cur.fetchall()
        weeks_order = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
        monthly_map = {r['week_bucket']: float(r['total_expense']) for r in monthly_rows} if monthly_rows else {}
        
        x_vals = weeks_order
        y_vals = [monthly_map.get(w, 0.0) for w in weeks_order]
        
    cur.close()
    conn.close()

    # Dynamic Dual-Mode Plotly Line Graph (Strict Y-Axis Max Limit: 5000)
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        name='Expense',
        mode='lines+markers',
        line=dict(color='#279655', width=3, shape='spline'),
        marker=dict(size=7, color='#279655', symbol='circle'),
        fill='tozeroy',
        fillcolor='rgba(39, 150, 85, 0.08)',
        hovertemplate="<b>%{x}</b><br>Expense: ₹%{y:,.2f}<extra></extra>"
    ))

    fig_line.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#1E293B'),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0, 0, 0, 0.05)',
            linecolor='#94A3B8',
            linewidth=1.5,
            tickfont=dict(size=12, color='#1E293B', family='Inter, sans-serif'),
            title=None
        ),
        yaxis=dict(
            range=[0, 5000],
            autorange=False,
            showgrid=True,
            gridcolor='rgba(0, 0, 0, 0.05)',
            linecolor='#94A3B8',
            linewidth=1.5,
            tickprefix='₹',
            tickfont=dict(size=12, color='#1E293B', family='Inter, sans-serif'),
            title=None
        ),
        margin=dict(t=15, b=25, l=15, r=15),
        hovermode="x unified"
    )
    st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
    
    # Detailed Trend Expense Breakdown List below Line Chart (No Percentage)
    st.markdown('<hr style="margin: 16px 0 12px 0; border-top: 1px solid #E2E8F0;">', unsafe_allow_html=True)
    breakdown_title = "Week-wise Expense Breakdown" if expense_window == "Monthly" else "Day-wise Expense Breakdown"
    st.markdown(f'<div style="font-weight: 700; font-size: 14px; color: #1E293B; margin-bottom: 10px;">{breakdown_title}</div>', unsafe_allow_html=True)
    
    full_day_names = {
        'Mon': 'Monday',
        'Tue': 'Tuesday',
        'Wed': 'Wednesday',
        'Thu': 'Thursday',
        'Fri': 'Friday',
        'Sat': 'Saturday',
        'Sun': 'Sunday'
    }

    for x_label, y_amount in zip(x_vals, y_vals):
        display_label = full_day_names.get(x_label, x_label) if expense_window == "Weekly" else x_label
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; margin-bottom: 6px; background-color: #F8FAFC; border-radius: 8px; border: 1px solid #F1F5F9;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #279655;"></span>
                    <span style="font-weight: 600; font-size: 13.5px; color: #1E293B;">{display_label}</span>
                </div>
                <div>
                    <span style="font-weight: 700; font-size: 14px; color: #0F172A;">₹{y_amount:,.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# Real-time mutations (Transaction Add Form)
# Dynamic Inline Actions & Forms handling
def delete_transaction(tx_id):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM transactions WHERE id = %s", (tx_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Error deleting transaction: {e}")
    finally:
        cur.close()
        conn.close()

def update_transaction(tx_id, amount, category, date, description):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE transactions SET amount = %s, category = %s, date = %s, description = %s WHERE id = %s",
            (amount, category, date, description, tx_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Error updating transaction: {e}")
    finally:
        cur.close()
        conn.close()

# Fetch expense history log — filtered to active calendar month (historical data preserved in DB)
conn = get_db_conn()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute(
    """
    SELECT id as transaction_id, TO_CHAR(date, 'MM-DD-YYYY') as formatted_date, date, category, description as notes, amount 
    FROM transactions 
    WHERE user_id = %s
      AND type = 'Expense'
      AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
      AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
    ORDER BY created_at DESC, id DESC
    """,
    (uid,)
)
expense_history = cur.fetchall()
cur.close()
conn.close()

# Section header for Expense History Log
st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 15px; margin-bottom: 25px;">
        <h3 style="margin: 0; font-size: 22px; font-weight: 700; color: #1A202C;">Expense History Log</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# Modal/Dialog Form for Add Expense button using st.dialog
@st.dialog("Add Expense")
def show_add_expense_dialog():
    st.write("Enter details of your expense transaction.")
    
    desc_val = st.text_input("Description / Title *", placeholder="e.g., Starbucks Coffee, Uber, Rent")
    
    # 2. Smart Category Classification Engine
    inferred_category = "Other"
    d_lower = desc_val.lower()
    
    # Classification rules
    dining_keywords = ['starbucks', 'restaurant', 'cafe', 'zomato', 'swiggy', 'mcdonalds', 'dinner', 'lunch', 'food']
    grocery_keywords = ['supermarket', 'walmart', 'grocery', 'milk', 'vegetables', 'instamart', 'zepto']
    ent_keywords = ['netflix', 'cinema', 'movies', 'spotify', 'concert', 'party', 'gaming']
    home_keywords = ['rent', 'electricity', 'water bill', 'wifi', 'internet', 'maintenance', 'plumber']
    shopping_keywords = ['amazon', 'zara', 'clothes', 'shoes', 'electronics', 'mall']
    travel_keywords = ['uber', 'flight', 'hotel', 'petrol', 'gas', 'train', 'airbnb']
    
    if any(k in d_lower for k in dining_keywords):
        inferred_category = "Dining"
    elif any(k in d_lower for k in grocery_keywords):
        inferred_category = "Groceries"
    elif any(k in d_lower for k in ent_keywords):
        inferred_category = "Entertainment"
    elif any(k in d_lower for k in home_keywords):
        inferred_category = "Home Essentials"
    elif any(k in d_lower for k in shopping_keywords):
        inferred_category = "Shopping"
    elif any(k in d_lower for k in travel_keywords):
        inferred_category = "Travel"

    categories = ["Dining", "Groceries", "Entertainment", "Home Essentials", "Shopping", "Travel", "Other"]
    default_idx = categories.index(inferred_category)
    
    category = st.selectbox("Category (Auto-classified, override if needed) *", categories, index=default_idx)
    
    amount = st.number_input("Amount (₹) *", min_value=0.0, value=None, step=0.5, placeholder="Enter amount...", format="%.2f")
    date = st.date_input("Date *", value=datetime.today().date(), max_value=datetime.today().date())
    payment_mode = st.selectbox("Payment Method *", ["UPI", "Credit Card", "Bank Transfer", "Cash"])
    notes = st.text_area("Notes (Optional)", placeholder="Extra transaction details...")
    
    if st.button("Save Expense", key="btn_save_expense_modal", use_container_width=True):
        if not desc_val:
            st.error("Description / Title is required!")
            return
        if date > datetime.today().date():
            st.error("Invalid Date: You cannot log expenses for future dates.")
            return
        add_transaction(uid, amount, 'Expense', category, date, desc_val, payment_mode)
        st.success("Expense saved successfully!")
        st.rerun()

if st.button("+ Add Expense", key="btn_add_expense_main", use_container_width=True):
    show_add_expense_dialog()

# Inline Editor state check
if 'edit_tx_id' in st.session_state:
    st.markdown("---")
    with st.form("edit_expense_form", clear_on_submit=True):
        st.subheader(f"Edit Transaction (ID: {st.session_state['edit_tx_id']})")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            edit_amount = st.number_input("Amount (₹) *", min_value=0.0, value=float(st.session_state['edit_amount']), step=0.5, format="%.2f")
            edit_date = st.date_input("Date *", value=st.session_state['edit_date'], max_value=datetime.today().date())
        with col_e2:
            edit_cat = st.selectbox("Category *", ["Dining", "Groceries", "Entertainment", "Home Essentials", "Shopping", "Travel", "Other"], index=["Dining", "Groceries", "Entertainment", "Home Essentials", "Shopping", "Travel", "Other"].index(st.session_state['edit_category']) if st.session_state['edit_category'] in ["Dining", "Groceries", "Entertainment", "Home Essentials", "Shopping", "Travel", "Other"] else 6)
            edit_desc = st.text_input("Description / Notes", value=st.session_state['edit_notes'])
            
        col_btns1, col_btns2 = st.columns(2)
        with col_btns1:
            saved = st.form_submit_button("Update Record")
            if saved:
                if edit_date > datetime.today().date():
                    st.error("Invalid Date: You cannot log expenses for future dates.")
                else:
                    update_transaction(st.session_state['edit_tx_id'], edit_amount, edit_cat, edit_date, edit_desc)
                    del st.session_state['edit_tx_id']
                    st.success("Transaction updated successfully!")
                    st.rerun()
        with col_btns2:
            cancelled = st.form_submit_button("Cancel Edit")
            if cancelled:
                del st.session_state['edit_tx_id']
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="expense-table-wrapper">', unsafe_allow_html=True)

# Render logs list
if not expense_history:
    # 2. Empty State Handling
    st.markdown(
        """
        <div style="text-align: center; padding: 40px 20px;">
            <div style="font-size: 64px; margin-bottom: 15px;">📋</div>
            <h4 style="color: #16222D; font-size: 18px; font-weight: 600; margin-bottom: 8px;">No Expense History Found</h4>
            <p style="color: #6B7280; font-size: 14px; margin: 0;">Log your first expense transaction above to start tracking your financial history.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # Render table header
    cols_h = st.columns([2, 2, 3, 2, 2.5])
    with cols_h[0]:
        st.markdown("**Date**")
    with cols_h[1]:
        st.markdown("**Category**")
    with cols_h[2]:
        st.markdown("**Notes**")
    with cols_h[3]:
        st.markdown("**Price**")
    with cols_h[4]:
        st.markdown("**Actions**")
        
    st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    # Render table rows
    for tx in expense_history:
        cols = st.columns([2, 2, 3, 2, 2.5])
        
        with cols[0]:
            st.markdown(f"<span style='font-weight: bold; color: #111827;'>{tx['formatted_date']}</span>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"<span style='color: #4B5563;'>{tx['category']}</span>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"<span style='color: #6B7280;'>{tx['notes'] or ''}</span>", unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"<span style='font-weight: bold; color: #84CC16;'>₹{float(tx['amount']):,.2f}</span>", unsafe_allow_html=True)
        with cols[4]:
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("Edit", key=f"edit_{tx['transaction_id']}", use_container_width=True):
                    st.session_state['edit_tx_id'] = tx['transaction_id']
                    st.session_state['edit_amount'] = tx['amount']
                    st.session_state['edit_date'] = tx['date']
                    st.session_state['edit_category'] = tx['category']
                    st.session_state['edit_notes'] = tx['notes'] or ''
                    st.rerun()
            with col_act2:
                if st.button("Delete", key=f"delete_{tx['transaction_id']}", use_container_width=True):
                    delete_transaction(tx['transaction_id'])
                    st.success("Transaction deleted successfully!")
                    st.rerun()
        st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #F3F4F6;'>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
import os
import base64
from datetime import datetime
import requests
import math
import random
import string
import time
import streamlit.components.v1 as components
# NEW: Import Captcha
from captcha.image import ImageCaptcha
# NEW: Import Supabase Client
from supabase import create_client, Client

# ==========================================
# 1. PRO CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="YieldMap Pro",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. SUPABASE CONNECTION & AUTH HANDLER
# ==========================================
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to Database: {e}")
        return None

supabase = init_connection()

# --- HELPER: JAVASCRIPT REDIRECT (For Email Link Only) ---
def js_redirect(url):
    redirect_code = f"""
    <script>
        window.top.location.href = "{url}";
    </script>
    <meta http-equiv="refresh" content="0;url={url}">
    """
    components.html(redirect_code, height=0, width=0)

# --- FIX: HANDLE EMAIL CONFIRMATION CODE ---
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        session = supabase.auth.exchange_code_for_session({"auth_code": code})
        st.session_state.user = session.user
        st.query_params.clear()
        # Redirect to main app URL to clear params and load clean
        js_redirect("https://yieldmappro.com/app")
        st.stop()
    except Exception as e:
        pass

# ==========================================
# 3. VISUAL UPGRADE: CUSTOM CSS
# ==========================================
st.markdown(
    """
    <style>
    /* 1. GLOBAL RESET & FONTS */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #1e293b; /* Slate 800 */
    }

    /* 2. LAYOUT & SPACING */
    .block-container {
        padding-top: 7rem;
        padding-bottom: 5rem;
    }

    /* 3. THE "TITAN BAR" (The Footer Cover-Up) */
    .titan-bar {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100vw;
        height: 50px; 
        background-color: #ffffff; /* Matches app background */
        z-index: 2147483647; 
        pointer-events: auto;
    }

    /* 4. AGGRESSIVE HIDING */
    header { visibility: hidden !important; }
    footer { visibility: hidden !important; display: none !important; }
    #MainMenu { display: none !important; }
    
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; }
    
    button[title="View fullscreen"] { display: none !important; }
    [data-testid="StyledFullScreenButton"] { display: none !important; }
    .viewerBadge_container__1QSob { display: none !important; }

    /* 5. THE STICKY HEADER BACKGROUND */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 80px;
        background-color: #1e3a8a; /* Deep Corporate Blue */
        z-index: 100000;
        display: flex;
        align-items: center;
        padding: 0 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-bottom: none;
    }

    /* 6. BRANDING */
    .brand-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-right: 40px;
        z-index: 100003;
    }
    .brand-title {
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1;
        cursor: default;
    }
    .brand-subtitle {
        font-size: 11px;
        font-weight: 400;
        color: #93c5fd;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 4px;
        cursor: default;
    }

    /* 7. NAVIGATION BAR STYLING */
    div[data-testid="stRadio"] {
        position: fixed;
        top: 20px;
        left: 300px;
        z-index: 100002;
        background-color: transparent;
        width: auto;
        height: 40px;
    }
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] label {
        background-color: transparent !important;
        border: none !important;
        margin-right: 20px !important;
        padding: 8px 16px !important;
        border-radius: 20px !important;
        transition: all 0.2s ease;
    }
    div[role="radiogroup"] p {
        font-size: 15px !important;
        font-weight: 500 !important;
        color: rgba(255, 255, 255, 0.7) !important;
    }
    div[role="radiogroup"] label:hover p { color: #ffffff !important; }
    div[role="radiogroup"] label[data-checked="true"] { background-color: rgba(255, 255, 255, 0.15) !important; }
    div[role="radiogroup"] label[data-checked="true"] p { color: #ffffff !important; font-weight: 700 !important; }

    /* 8. UNIVERSAL BUTTON STYLING */
    [data-testid="stButton"] button, 
    [data-testid="stDownloadButton"] button,
    [data-testid="stFormSubmitButton"] button {
        background-color: #1e3a8a !important; 
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
    }
    [data-testid="stButton"] button:hover, 
    [data-testid="stDownloadButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        background-color: #1e40af !important;
        color: #ffffff !important;
    }
    a[data-testid="stLinkButton"] {
        background-color: #1e3a8a !important; 
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        font-weight: 600 !important;
        text-decoration: none !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 0.5rem 1rem !important;
    }
    a[data-testid="stLinkButton"] * { color: #ffffff !important; font-weight: 600 !important; }
    a[data-testid="stLinkButton"]:hover { background-color: #1e40af !important; color: #ffffff !important; }

    /* 9. CARDS & CONTAINERS */
    .stExpander, .element-container { border-radius: 8px; }
    h1, h2, h3, h4, h5 { color: #0f172a; font-weight: 700; letter-spacing: -0.025em; }

    /* 10. MOBILE RESPONSIVENESS */
    @media (max-width: 900px) {
        .brand-subtitle { display: none; }
        div[data-testid="stRadio"] {
            top: 80px; left: 0; width: 100%;
            background-color: #f1f5f9; padding: 10px;
            display: flex; justify-content: center;
        }
        div[role="radiogroup"] p { color: #64748b !important; }
        div[role="radiogroup"] label[data-checked="true"] { background-color: #1e3a8a !important; }
        div[role="radiogroup"] label[data-checked="true"] p { color: white !important; }
        .block-container { padding-top: 10rem; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# INJECT THE TITAN BAR OVERLAY
st.markdown('<div class="titan-bar"></div>', unsafe_allow_html=True)

# ==========================================
# 4. REFERENCE DATA (STATE MAP)
# ==========================================
STATE_MAP = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia"
}

# ==========================================
# 5. DATA UTILITIES
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("hud_2026.xlsx", header=0, dtype=str)
        df.columns = df.columns.astype(str).str.replace('\n', '_').str.replace(' ', '_').str.upper().str.strip()
        if 'ZIP_CODE' in df.columns: df = df.dropna(subset=['ZIP_CODE'])
        
        rename_map = {'ZIP_CODE': 'zip_code', 'ZIP': 'zip_code', 'SAFMR_0BR': 'Studio', 'SAFMR_1BR': '1-Bedroom', 'SAFMR_2BR': '2-Bedroom', 'SAFMR_3BR': '3-Bedroom', 'SAFMR_4BR': '4-Bedroom', 'HUD_FAIR_MARKET_RENT_AREA_NAME': 'area_name'}
        available_cols = [c for c in rename_map.keys() if c in df.columns]
        df = df[available_cols].rename(columns=rename_map)
        df['state_abbr'] = df['area_name'].str.extract(r',\s([A-Z]{2})')
        df['state'] = df['state_abbr'].map(STATE_MAP).fillna('Other')

        for c in ['Studio', '1-Bedroom', '2-Bedroom', '3-Bedroom', '4-Bedroom']:
            if c in df.columns: df[c] = pd.to_numeric(df[c].str.replace('$', '').str.replace(',', ''), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"CRITICAL ERROR loading data: {e}"); return pd.DataFrame()

@st.cache_data(ttl=86400)
def get_vacancy_rate(zip_code):
    try:
        time.sleep(0.5) 
        url_rate = f"https://api.census.gov/data/2023/acs/acs5/profile?get=DP04_0005PE&for=zip%20code%20tabulation%20area:{zip_code}"
        r = requests.get(url_rate, timeout=3)
        data = r.json()
        if len(data) > 1 and data[1][0]: return float(data[1][0])
    except: pass 

    try:
        url_raw = f"https://api.census.gov/data/2023/acs/acs5?get=B25004_002E,B25003_003E&for=zip%20code%20tabulation%20area:{zip_code}"
        r = requests.get(url_raw, timeout=3)
        data = r.json()
        if len(data) > 1:
            vacant_for_rent = float(data[1][0]); renter_occupied = float(data[1][1])
            total = vacant_for_rent + renter_occupied
            if total > 0: return round((vacant_for_rent / total) * 100, 1)
    except: pass 
    return 5.0

# ==========================================
# 6. MATH ENGINES
# ==========================================
def calculate_mortgage(price, down_payment_pct, interest_rate, term_years=30):
    loan_amount = price * (1 - (down_payment_pct/100))
    if loan_amount <= 0: return 0
    monthly_rate = (interest_rate / 100) / 12; num_payments = term_years * 12
    if monthly_rate == 0: return loan_amount / num_payments
    return loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)

def calculate_max_offer(net_rent, target_coc, repairs, closing_costs_pct, down_pct, interest_rate, taxes, insurance, maint_monthly, pm_monthly):
    test_price = 50000; step = 1000
    for _ in range(1000): 
        loan = test_price * (1 - down_pct/100)
        monthly_pmt = calculate_mortgage(test_price, down_pct, interest_rate)
        cashflow_yr = (net_rent - (taxes/12) - (insurance/12) - maint_monthly - pm_monthly - monthly_pmt) * 12
        investment = (test_price * down_pct/100) + (test_price * closing_costs_pct/100) + repairs
        coc = (cashflow_yr / investment) * 100 if investment > 0 else 0
        if coc < target_coc: return test_price - step 
        test_price += step
    return 0

def calculate_projections(price, rent, total_expenses_yr, mortgage_yr, down_pct, interest_rate, term_years, rent_growth, appreciation):
    data = []
    current_rent = rent * 12; current_expenses = total_expenses_yr
    loan_balance = price * (1 - down_pct/100)
    for year in range(1, 31):
        noi = current_rent - current_expenses; cashflow = noi - mortgage_yr
        if loan_balance > 0:
            interest_payment = loan_balance * (interest_rate/100)
            principal_payment = mortgage_yr - interest_payment
            if principal_payment > loan_balance: principal_payment = loan_balance
            loan_balance -= principal_payment
        property_value = price * ((1 + appreciation/100)**year)
        data.append({"Year": year, "Cash Flow": cashflow, "Loan Balance": loan_balance, "Total Equity": property_value - loan_balance})
        current_rent *= (1 + rent_growth/100); current_expenses *= (1 + rent_growth/100)
    return pd.DataFrame(data)

# ==========================================
# 7. MULTI-PAGE PDF GENERATOR (REBUILT FOR DETAIL)
# ==========================================
class ProPDF(FPDF):
    def header(self):
        # Header Box
        self.set_fill_color(30, 58, 138) # Corporate Blue
        self.rect(0, 0, 210, 30, 'F')
        
        # Logo Text
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 8)
        self.cell(0, 10, "YieldMap Pro", 0, 0, 'L')
        
        # Report Title
        self.set_font('Helvetica', '', 12)
        self.set_text_color(147, 197, 253) # Light Blue
        self.set_xy(10, 18)
        self.cell(0, 6, "SECTION 8 INTELLIGENCE REPORT", 0, 0, 'L')
        
        # Date
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(160, 10)
        self.cell(40, 10, datetime.now().strftime('%Y-%m-%d'), 0, 0, 'R')
        
        # Watermark (Subtle)
        self.set_font('Helvetica', 'B', 50)
        self.set_text_color(240, 240, 240)
        self.set_xy(0, 140)
        self.cell(210, 0, "CONFIDENTIAL", 0, 0, 'C')
        
        self.ln(25) # Push cursor down below header

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'YieldMap Pro | Generated for Pro Members | Page {self.page_no()} of {{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        self.ln(5)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(30, 58, 138)
        self.cell(0, 8, title, 0, 1, 'L')
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def section_header(self, title):
        self.ln(3)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 6, title, 0, 1, 'L')

    def kpi_box(self, label, value, x, y):
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(200, 200, 200)
        self.rect(x, y, 45, 25, 'DF')
        self.set_xy(x, y+5)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(45, 5, label, 0, 1, 'C')
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(30, 58, 138)
        self.cell(45, 8, value, 0, 1, 'C')

    def add_row(self, col1, col2, is_total=False):
        self.set_font('Helvetica', 'B' if is_total else '', 10)
        fill = True if is_total else False
        self.set_fill_color(240, 249, 255) # Light Blue fill
        self.set_text_color(0, 0, 0)
        
        self.cell(140, 7, col1, 1, 0, 'L', fill)
        self.cell(50, 7, col2, 1, 1, 'R', fill)

def generate_pro_report(client, address, row, unit, price, rent, v_rate, yield_val, coc_return, net_cashflow, d_grade, n_grade, down_pct, int_rate, taxes, ins, maint_cost, loan_pmt, hud_limit, ua_val, maint_pct, pm_pct, term_years, repairs, projections_df, rent_growth, appreciation, closing_costs):
    pdf = ProPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- PAGE 1: EXECUTIVE SUMMARY ---
    
    # 1. Subject Property Box
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 58, 138)
    area_name = row.get('area_name', 'Unknown')
    pdf.cell(0, 10, f"Analysis: {address}", 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, f"Market Area: {area_name} | Unit Type: {unit}", 0, 1, 'L')
    pdf.cell(0, 5, f"Prepared For: {client if client else 'Valued Client'}", 0, 1, 'L')
    pdf.ln(5)

    # 2. KPI GRID (Top Row)
    y_kpi = pdf.get_y()
    pdf.kpi_box("Cash-on-Cash", f"{coc_return:.1f}%", 10, y_kpi)
    pdf.kpi_box("Monthly Flow", f"${net_cashflow:,.0f}", 60, y_kpi)
    pdf.kpi_box("Cap Rate", f"{yield_val:.1f}%", 110, y_kpi)
    
    # DSCR Calculation
    dscr = 0
    if loan_pmt > 0:
        dscr = ((rent * (1 - v_rate/100)) - (taxes/12 + ins/12 + maint_cost + rent*(pm_pct/100))) / loan_pmt
    pdf.kpi_box("DSCR Ratio", f"{dscr:.2f}x", 160, y_kpi)
    
    pdf.set_y(y_kpi + 35)

    # 3. DEAL GRADES
    pdf.chapter_title("Investment Grade Scorecard")
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(95, 8, f"Neighborhood Rating: {n_grade}", 1, 0, 'C')
    pdf.cell(95, 8, f"Deal Performance: {d_grade}", 1, 1, 'C')
    pdf.ln(5)

    # 4. CAPITAL REQUIREMENTS (Cash to Close)
    pdf.chapter_title("Capital Requirements (Cash to Close)")
    down_amt = price * (down_pct / 100)
    closing_amt = price * (closing_costs / 100)
    total_cash = down_amt + closing_amt + repairs
    
    pdf.add_row(f"Down Payment ({down_pct}%)", f"${down_amt:,.0f}")
    pdf.add_row(f"Estimated Closing Costs ({closing_costs}%)", f"${closing_amt:,.0f}")
    pdf.add_row("Immediate Repairs / HQS Prep", f"${repairs:,.0f}")
    pdf.add_row("TOTAL CASH REQUIRED", f"${total_cash:,.0f}", True)

    # 5. INCOME & EXPENSE STATEMENT
    pdf.chapter_title("Pro Forma Monthly Operating Statement")
    
    # Income
    pdf.section_header("Income")
    pdf.add_row("Gross Market Rent (HUD FMR)", f"${rent:,.2f}")
    pdf.add_row(f"Vacancy Allowance ({v_rate}%)", f"(${rent * (v_rate/100):,.2f})")
    pdf.add_row("EFFECTIVE GROSS INCOME", f"${rent * (1 - v_rate/100):,.2f}", True)
    
    # Expenses
    pdf.section_header("Operating Expenses")
    pdf.add_row("Property Taxes", f"(${taxes/12:,.2f})")
    pdf.add_row("Insurance", f"(${ins/12:,.2f})")
    pdf.add_row(f"Maintenance Reserves ({maint_pct}%)", f"(${maint_cost:,.2f})")
    pdf.add_row(f"Property Management ({pm_pct}%)", f"(${rent * (pm_pct/100):,.2f})")
    
    # NOI
    noi_val = (rent * (1 - v_rate/100)) - (taxes/12 + ins/12 + maint_cost + rent*(pm_pct/100))
    pdf.add_row("NET OPERATING INCOME (NOI)", f"${noi_val:,.2f}", True)
    
    # Debt Service
    pdf.section_header("Debt Service")
    pdf.add_row(f"Mortgage Payment ({interest_rate}% @ {term_years}yrs)", f"(${loan_pmt:,.2f})")
    
    # Final CF
    pdf.ln(2)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(140, 10, "ESTIMATED NET MONTHLY CASH FLOW", 1, 0, 'L', True)
    pdf.cell(50, 10, f"${net_cashflow:,.2f}", 1, 1, 'R', True)

    # --- PAGE 2: WEALTH ACCUMULATION ---
    pdf.add_page()
    pdf.chapter_title("Long-Term Wealth Projections")
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 6, f"This analysis assumes a {rent_growth}% annual increase in rents and a {appreciation}% annual property appreciation rate. It accounts for loan paydown (amortization) and cash flow reinvestment.")
    pdf.ln(5)

    # Headers
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(20, 8, "Year", 1, 0, 'C', True)
    pdf.cell(40, 8, "Annual CF", 1, 0, 'C', True)
    pdf.cell(40, 8, "Loan Balance", 1, 0, 'C', True)
    pdf.cell(40, 8, "Property Equity", 1, 0, 'C', True)
    pdf.cell(50, 8, "Total Wealth Created", 1, 1, 'C', True)

    # Rows
    pdf.set_text_color(50, 50, 50)
    pdf.set_font('Helvetica', '', 9)
    
    snapshot_years = [1, 2, 3, 5, 7, 10, 15, 20, 30]
    cumulative_cf = 0
    
    for index, r in projections_df.iterrows():
        yr = int(r['Year'])
        cumulative_cf += r['Cash Flow']
        
        if yr in snapshot_years:
            # Total Wealth = Equity + Cumulative Cash Flow - Initial Investment
            total_wealth = r['Total Equity'] + cumulative_cf - total_cash
            
            pdf.cell(20, 8, str(yr), 1, 0, 'C')
            pdf.cell(40, 8, f"${r['Cash Flow']:,.0f}", 1, 0, 'C')
            pdf.cell(40, 8, f"${r['Loan Balance']:,.0f}", 1, 0, 'C')
            pdf.cell(40, 8, f"${r['Total Equity']:,.0f}", 1, 0, 'C')
            pdf.cell(50, 8, f"${total_wealth:,.0f}", 1, 1, 'C')

    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.multi_cell(0, 5, "Disclaimer: These projections are theoretical and for educational purposes. They assume constant market conditions and do not account for major unforeseen CapEx events.")

    return pdf.output(dest='S')

def create_gauge(value, title, min_v, max_v, suffix="%", flip=False):
    colors = ["#fee2e2", "#fef3c7", "#d1fae5"]
    if flip:
        colors = ["#d1fae5", "#fef3c7", "#fee2e2"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': suffix, 'font': {'size': 35}},
        gauge={
            'axis': {'range': [min_v, max_v]},
            'bar': {'color': "#2563eb"},
            'steps': [
                {'range': [min_v, max_v * 0.33], 'color': colors[0]},
                {'range': [max_v * 0.33, max_v * 0.66], 'color': colors[1]},
                {'range': [max_v * 0.66, max_v], 'color': colors[2]}
            ]
        }
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=40, r=40, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def render_footer():
    st.divider()
    st.markdown(
        """
        <div style="text-align: center; font-size: 12px; color: #64748b;">
            <p><strong>Yieldmappro.com</strong> | © 2025 All Rights Reserved</p>
            <p>Data Source: U.S. Housing & Urban Development (HUD) FY 2026 Small Area FMRs</p>
            <p style="font-style: italic;">Disclaimer: This tool is for educational purposes only and does not constitute financial advice. Always verify data with your local Housing Authority.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# 8. INITIALIZE DATABASE & STATE
# ==========================================
if 'user' not in st.session_state:
    st.session_state.user = None
if 'ua_value' not in st.session_state:
    st.session_state.ua_value = 150
if 'captcha_text' not in st.session_state:
    # UPDATED CAPTCHA CHARACTERS TO REMOVE AMBIGUITY (No 0, O, I, 1)
    st.session_state.captcha_text = ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=5))
# NEW: AUTH PAGE STATE HANDLER
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'

# ==========================================
# 9. AUTHENTICATION & HEADER
# ==========================================
st.markdown(
    """
    <div class="fixed-header">
        <div class="brand-container">
            <div class="brand-title">YieldMap Pro</div>
            <div class="brand-subtitle">Section 8 Intelligence • FY 2026</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# DIALOG FUNCTION FOR TERMS
@st.dialog("Terms of Service")
def show_terms():
    st.markdown("""
### Terms of Use
**Last Updated: December 30, 2025**

**Introduction**
YieldMap Pro is provided by [Your Company Name/LLC], located in [Your Location, e.g., USA]. These Terms of Use govern your access to and use of our website, services, and tools. By using YieldMap Pro, you agree to these terms.

**1. Acceptance of Terms**
By accessing YieldMap Pro, you agree to be bound by these Terms of Use. This agreement governs your use of our underwriting dashboard, data exports, and audit reports.

**2. No Professional Advice**
YieldMap Pro is an analytical tool for informational purposes only. We do not provide financial, legal, tax, or real estate investment advice.
All deal grades (A-F), ROI percentages, and cash flow projections are estimates based on your manual inputs and historical government data. You should perform your own independent due diligence before making any financial commitments.

**3. Data Accuracy & HUD Compliance**
While we use official federal data sources (HUD User API and US Census), local Housing Authorities (PHAs) have the final authority to set voucher payment standards. YieldMap Pro does not guarantee that a specific PHA will approve the exact contract rent calculated by our tool.

**4. Usage Restrictions**
You are granted a non-exclusive license to use this tool for professional underwriting. You agree not to:
* Scrape data from our interface for use in competing products.
* Attempt to reverse-engineer our proprietary Asset Rating logic.
* Redistribute "Investor Pro" features or PDF reports without a valid subscription.

**Intellectual Property**
All content, features, and functionality (including software, algorithms, and data integrations) are owned by YieldMap Pro or its licensors and protected by intellectual property laws. You may not copy, modify, or distribute any part without written permission.

**5. Limitation of Liability**
YieldMap Pro shall not be liable for any financial losses, investment failures, or damages arising from your reliance on our projections. All calculations are provided "as-is" without warranty of any kind.

**Indemnification**
You agree to indemnify and hold harmless YieldMap Pro, its affiliates, and employees from any claims, damages, or expenses arising from your misuse of the service or violation of these terms.

**6. Subscription & Cancellation**
Investor Pro subscriptions are billed monthly. You may cancel at any time via your dashboard. Fees already paid are non-refundable for the current billing cycle.

**Dispute Resolution**
Any disputes arising from these terms will be resolved through binding arbitration in [Your Location, e.g., California], under the rules of [e.g., AAA]. You waive the right to class actions.

**Governing Law**
These terms are governed by the laws of [Your State/Country, e.g., the United States and the State of California], without regard to conflict of law principles.

**Changes to Terms**
We may update these terms periodically. We will notify you via email or site notice for material changes. Continued use constitutes acceptance.
    """)

# DIALOG FUNCTION FOR PRIVACY
@st.dialog("Privacy Policy")
def show_privacy():
    st.markdown("""
### Privacy Policy
**Last Updated: December 30, 2025**

**Introduction**
YieldMap Pro is a Section 8 deal analysis tool provided by [Your Company Name/LLC], located in [Your Location, e.g., USA]. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our website and services. By using YieldMap Pro, you agree to the practices described here.

**1. Data Philosophy**
At YieldMap Pro, we believe your investment strategy is your own business. Unlike mainstream listing scrapers, we prioritize a "Privacy-First" underwriting environment. We do not sell your deal data to third-party brokers or lenders.

**2. Information We Collect**
* **Account Information:** Email addresses provided during Pro registration are used solely for account management and support.
* **Usage Data:** We use basic analytics to monitor tool performance and ensure federal API connection stability.
* **Underwriting Data:** Input values like "Target Contract Rent" or "Interest Rate" are processed in-session. We do not permanently store specific property addresses on our public-tier servers.

**How We Use Your Information**
* To provide and improve our services, such as generating reports and analyzing deals.
* For internal analytics to enhance tool performance and user experience.
* To communicate with you about updates, support, or account-related matters.
* To comply with legal obligations, such as responding to subpoenas.

**Data Sharing and Disclosure**
We do not sell or rent your personal information. We may share data with:
* Service providers (e.g., hosting, analytics) under strict confidentiality agreements.
* Government APIs (HUD, Census) as described, but only anonymized queries.
* Legal authorities if required by law.
We do not engage in targeted advertising or share data for marketing purposes.

**Cookies and Tracking Technologies**
We use essential cookies for session management and basic analytics (e.g., via Google Analytics). These help us understand usage patterns without identifying individuals. You can manage cookies via your browser settings, but disabling them may limit functionality.

**3. Federal API Integrations**
YieldMap Pro connects directly to the **HUD User API** and **US Census Bureau ACS Survey**. When you query a ZIP code, your request is sent to these government servers to fetch the most recent FY 2026 data. These requests are anonymized.

**4. Security**
We use industry-standard SSL encryption for all data transmissions. Your "Lender-Ready PDF Reports" are generated locally in your browser session to ensure your deal numbers remain private until you choose to export them.

**Your Rights**
Depending on your location, you may have rights under laws like CCPA (California) or GDPR (EU):
* Access, correct, or delete your personal data.
* Opt-out of data sharing (though we don't sell data).
* Request information on data processing.
To exercise these rights, email support@yieldmappro.com. We respond within 30-45 days, as required by law.

**Children's Privacy**
YieldMap Pro is not intended for users under 18. We do not knowingly collect data from children. If we learn of such collection, we will delete it promptly.

**Changes to This Policy**
We may update this policy to reflect changes in our practices or laws. We will notify users via email or site notice for material changes. Continued use after updates constitutes acceptance.

**Governing Law**
This policy is governed by the laws of [Your State/Country, e.g., the United States and the State of California], without regard to conflict of law principles.

**5. Contact Us**
For questions regarding your data or to request account deletion, please contact us at:
support@yieldmappro.com
    """)

# --- NEW: AUTH CALLBACK FUNCTION (Bulletproof State Switching) ---
def switch_to_login_callback():
    st.session_state.auth_mode = 'login'
    # Clear signup keys just in case
    for key in list(st.session_state.keys()):
        if key.startswith("signup_"):
            del st.session_state[key]
    # No need to call st.rerun() here, button callback does it automatically

# NEW: SUCCESS DIALOG
@st.dialog("Account Created Successfully")
def show_success_modal():
    st.write("Your account has been created.")
    st.write("Please check your email to confirm your address.")
    
    # === THE FIX: Use native Streamlit button with callback ===
    st.button("OK, Go to Login", on_click=switch_to_login_callback)

# LOGIN LOGIC
if not st.session_state.user:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        # LOG IN FORM
        if st.session_state.auth_mode == 'login':
            with st.container(border=True):
                st.markdown("### Welcome Back")
                with st.form("login_form"):
                    email = st.text_input("Email", key="login_email")
                    password = st.text_input("Password", type="password", key="login_pass")
                    submitted = st.form_submit_button("Log In", type="primary")
                    if submitted:
                        try:
                            # FIX: Store the USER object
                            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.session_state.user = response.user 
                            st.rerun()
                        except Exception as e:
                            st.error(f"Login failed: {e}")
                
                st.markdown("---")
                if st.button("Don't have an account? Create one"):
                    st.session_state.auth_mode = 'signup'
                    st.rerun()

        # SIGN UP FORM
        else:
            with st.container(border=True):
                st.markdown("### New Account")
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_pass")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_pass")
                
                first_name = st.text_input("First Name", key="signup_fname")
                role = st.selectbox("I am a...", ["Investor", "Agent", "Wholesaler", "Property Manager", "Other"], key="signup_role")
                
                # CAPTCHA
                image = ImageCaptcha(width=280, height=90)
                data = image.generate(st.session_state.captcha_text)
                st.image(data)
                captcha_input = st.text_input("Enter the code above:", key="captcha_input")
                
                # TERMS
                st.markdown("---")
                c_check, c_terms, c_priv = st.columns([0.1, 0.45, 0.45])
                with c_check:
                    tos_agreed = st.checkbox("", label_visibility="collapsed")
                with c_terms:
                    if st.button("📄 Read Terms", use_container_width=True):
                        show_terms()
                with c_priv:
                    if st.button("🔒 Read Privacy", use_container_width=True):
                        show_privacy()
                
                st.caption("By checking the box, you agree to the Terms of Service and Privacy Policy.")

                if st.button("Create Account", type="primary"):
                    if not tos_agreed:
                        st.error("⚠️ You must agree to the Terms of Service.")
                    elif len(new_password) < 6:
                        st.error("⚠️ Password must be at least 6 characters.")
                    elif new_password != confirm_password:
                        st.error("⚠️ Passwords do not match.")
                    elif captcha_input.upper() == st.session_state.captcha_text:
                        try:
                            response = supabase.auth.sign_up({
                                "email": new_email, 
                                "password": new_password,
                                "options": {
                                    "data": {
                                        "first_name": str(first_name),
                                        "role": str(role)
                                    }
                                }
                            })
                            show_success_modal()
                        except Exception as e:
                            st.error(f"Registration failed: {str(e)}")
                    else:
                        st.error("❌ Incorrect CAPTCHA code.")
                        time.sleep(1.5)
                        st.session_state.captcha_text = ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=5))
                        st.rerun()
                
                st.markdown("---")
                if st.button("Already have an account? Log In"):
                    st.session_state.auth_mode = 'login'
                    st.rerun()
    st.stop()

# ==========================================
# 10. MAIN APP (AFTER LOGIN)
# ==========================================
with st.spinner("Loading Market Data..."):
    df = load_data()

if df.empty:
    st.error("DATABASE NOT FOUND: Please ensure 'hud_2026.xlsx' is uploaded.")
    st.stop()

# --- NAVIGATION ---
page = st.radio("Navigation", ["Pro Analyzer", "My Portfolio", "IQ Center"], horizontal=True, label_visibility="collapsed")

if page == "Pro Analyzer":
    # === WELCOME HEADER ===
    try:
        user_name = st.session_state.user.user_metadata.get('first_name', '')
        if not user_name:
            user_name = "Investor"
    except:
        user_name = "Investor"
    
    st.markdown(f"### Welcome, {user_name}")
    st.caption("Ready to find your next deal?")
    st.markdown("---")

    # ==========================================
    # TAB 1: PRO ANALYZER
    # ==========================================
    with st.container(border=True):
        st.markdown("#### 1. Property Details")
        c_client, c_addr = st.columns(2)
        with c_client:
            client_name = st.text_input("Prepared For", placeholder="e.g. Acme Properties LLC")
        with c_addr:
            prop_address = st.text_input("Property Address", placeholder="e.g. 123 Main St, Rome, GA")

        col_input1, col_input2, col_input3 = st.columns(3)

        with col_input1:
            state_list = sorted([s for s in df['state'].unique() if s != 'Other'])
            selected_state = st.selectbox("1. Select State", state_list, help="Filter markets by US State.")

        with col_input2:
            zip_list = sorted(df[df['state'] == selected_state]['zip_code'].unique())
            selected_zip = st.selectbox("2. Select ZIP Code", zip_list, help="Select the exact ZIP code from Zillow/Redfin.")

        with col_input3:
            beds = st.selectbox(
                "3. Unit Asset Class",
                ["Studio", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom"],
                index=2,
                help="Select bedroom count."
            )

    row = df[df['zip_code'] == selected_zip].iloc[0]
    market_area_name = row.get('area_name', 'Unknown Area')

    st.markdown("---")
    st.markdown(f"#### {market_area_name} ({selected_zip})")

    # SMART LINKS (No Emojis, Styled Links)
    c_link1, c_link2, c_link3 = st.columns(3)
    
    beds_url_str = beds.split('-')[0]
    zillow_url = f"https://www.zillow.com/homes/for_rent/{selected_zip}_rb/{beds_url_str}_beds/"
    rentometer_url = "https://www.rentometer.com/"
    pha_url = "https://www.hud.gov/program_offices/public_indian_housing/pha/contacts"

    with c_link1:
        st.link_button("View Zillow Comps", zillow_url, use_container_width=True)
    with c_link2:
        st.link_button("Check Rentometer", rentometer_url, use_container_width=True)
    with c_link3:
        st.link_button("Find Local PHA", pha_url, use_container_width=True)

    try:
        import pgeocode
        import folium
        from streamlit_folium import st_folium
        nomi = pgeocode.Nominatim('us')
        loc = nomi.query_postal_code(selected_zip)

        if not math.isnan(loc.latitude):
            if not math.isnan(loc.longitude):
                m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=13)
                folium.Marker(
                    [loc.latitude, loc.longitude],
                    icon=folium.Icon(color="blue", icon="home", prefix='fa')
                ).add_to(m)
                st_folium(m, height=350, use_container_width=True)
    except:
        pass

    st.markdown("---")
    limit = row[beds]

    # --- UA SECTION: Presets + Number Input ---
    with st.container(border=True):
        st.markdown(f"#### Utility Allowance Deduction")
        
        # PRESET BUTTONS
        col_presets = st.columns(3)
        with col_presets[0]:
            if st.button("Low ($120)"):
                st.session_state.ua_value = 120
        with col_presets[1]:
            if st.button("Mid ($180)"):
                st.session_state.ua_value = 180
        with col_presets[2]:
            if st.button("High ($250)"):
                st.session_state.ua_value = 250
        
        # DIRECT INPUT
        ua_input = st.number_input(
            "Enter Deduction Amount ($)",
            min_value=0,
            max_value=1000,
            value=st.session_state.ua_value,
            step=10,
            help="Consult local PHA for exact utility allowance schedule."
        )
        st.session_state.ua_value = ua_input

        target_rent = limit - ua_input
        st.info(f"**HUD Limit:** ${limit:,.0f}\n\n**Net Contract Rent:** ${target_rent:,.0f}")

    with st.container(border=True):
        st.markdown("#### Acquisition")
        c1, c2 = st.columns(2)
        with c1:
            price = st.number_input("Price", value=250000)
        with c2:
            rent_in = st.number_input("Rent", value=int(target_rent))

        api_vacancy = get_vacancy_rate(selected_zip)
        is_unlocked = True # Since user is logged in, features are unlocked

        # ADVANCED CONFIG (SECTION STYLE, NO EMOJI)
        with st.container(border=True):
            st.markdown("##### Financial Assumptions")
            
            c1, c2 = st.columns(2)
            with c1:
                user_vacancy = st.number_input("Vacancy %", value=5.0)
                down_payment = st.number_input("Down %", value=20.0)
                interest_rate = st.number_input("Rate %", value=7.0)
                loan_term_years = st.number_input("Term", value=30)
                initial_repairs = st.number_input("Repairs", value=2000)
                appreciation = st.number_input("Appreciation %", value=2.0)
                rent_growth = st.number_input("Rent Growth %", value=2.0)
            with c2:
                taxes_yr = st.number_input("Taxes", value=3000)
                insurance_yr = st.number_input("Insurance", value=1200)
                maint_capex = st.number_input("Maint/CapEx (%)", value=10.0, step=1.0)
                prop_mgmt_pct = st.number_input("Mgmt %", value=8.0)
                closing_costs = st.number_input("Closing %", value=3.0)
                target_coc_input = st.number_input("Target CoC", value=12.0)

    # CALCS
    gross = rent_in * 12
    vac_loss = gross * (user_vacancy / 100)
    egi = gross - vac_loss
    maint = egi * (maint_capex / 100)
    pm = gross * (prop_mgmt_pct / 100)
    exp = taxes_yr + insurance_yr + maint + pm
    noi = egi - exp
    mort = calculate_mortgage(price, down_payment, interest_rate, loan_term_years)
    debt = mort * 12
    cf = noi - debt
    invest = (price * down_payment / 100) + (price * closing_costs / 100) + initial_repairs

    coc = 0
    if invest > 0:
        coc = (cf / invest * 100)

    n_grade = "C"
    if limit >= 2500:
        n_grade = "A"
    elif limit >= 1800:
        n_grade = "B"

    d_grade = "C"
    if coc >= 12:
        d_grade = "A+"
    elif coc >= 8:
        d_grade = "B"

    st.divider()
    st.markdown("## Asset Rating")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Deal Grade", d_grade)
    r2.metric("CoC Return", f"{coc:.1f}%")
    r3.metric("Monthly CF", f"${cf / 12:,.0f}")
    r4.metric("Cash Needed", f"${invest:,.0f}")

    mao = calculate_max_offer(
        rent_in * (1 - user_vacancy / 100),
        target_coc_input,
        initial_repairs,
        closing_costs,
        down_payment,
        interest_rate,
        taxes_yr,
        insurance_yr,
        maint / 12,
        pm / 12
    )
    st.info(f"**Max Allowable Offer (MAO):** ${mao:,.0f} for {target_coc_input}% CoC")

    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(create_gauge(coc, "CoC %", 0, 20), use_container_width=True, config={'staticPlot': True})

    with g2:
        years = list(range(1, 6))
        equity_vals = []
        current_bal = price * (1 - down_payment / 100)
        for y in years:
            paid_principal = (mort * 12) - (current_bal * interest_rate / 100)
            if paid_principal < 0:
                paid_principal = 0
            current_bal -= paid_principal
            equity = price * ((1 + appreciation / 100)**y) - current_bal
            equity_vals.append(equity)
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(x=years, y=equity_vals, fill='tozeroy'))
        fig_eq.update_layout(
            height=180,
            margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_eq, use_container_width=True, config={'staticPlot': True})

    st.divider()

    e1, e2, e3 = st.columns(3)

    with e1:
        if st.button("Save Deal", type="primary", use_container_width=True):
            try:
                # DATABASE INSERT
                deal_data = {
                    "user_email": st.session_state.user.email,
                    "address": prop_address or f"ZIP {selected_zip}",
                    "price": price,
                    "rent": rent_in,
                    "coc": coc,
                    "cashflow": cf / 12,
                    "grade": d_grade
                }
                supabase.table("portfolios").insert(deal_data).execute()
                st.success("Saved to Portfolio!")
            except Exception as e:
                st.error(f"Error saving: {e}")

    with e2:
        proj = calculate_projections(
            price,
            rent_in,
            exp,
            debt,
            down_payment,
            interest_rate,
            loan_term_years,
            rent_growth,
            appreciation
        )
        pdf = generate_pro_report(
            client_name,
            prop_address,
            row,
            beds,
            price,
            rent_in,
            user_vacancy,
            0,
            coc,
            cf / 12,
            d_grade,
            n_grade,
            down_payment,
            interest_rate,
            taxes_yr,
            insurance_yr,
            maint,
            mort,
            limit,
            ua_input,
            maint_capex,
            prop_mgmt_pct,
            loan_term_years,
            initial_repairs,
            proj,
            rent_growth,
            appreciation,
            closing_costs
        )
        st.download_button(
            "Download Report",
            data=pdf.encode('latin-1'),
            file_name="Report.pdf",
            use_container_width=True
        )

    with e3:
        st.download_button(
            "Export Data",
            data=row.to_frame().T.to_csv().encode('utf-8'),
            file_name=f"Data_{selected_zip}.csv",
            use_container_width=True
        )

elif page == "My Portfolio":
    # ==========================================
    # TAB 2: PORTFOLIO (REAL DATABASE)
    # ==========================================
    st.header("Portfolio Command Center")
    
    # FETCH DATA
    try:
        response = supabase.table("portfolios").select("*").eq("user_email", st.session_state.user.email).execute()
        deals = response.data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        deals = []

    if not deals:
        st.info("No deals saved. Go to the **Pro Analyzer** tab to run a deal.")
    else:
        # ANALYTICS SUMMARY
        t_cf = sum(d['cashflow'] for d in deals)
        avg_c = sum(d['coc'] for d in deals) / len(deals)
        t_val = sum(d['price'] for d in deals)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Monthly CF", f"${t_cf:,.0f}")
        c2.metric("Portfolio Value", f"${t_val:,.0f}")
        c3.metric("Avg Portfolio CoC", f"{avg_c:.1f}%")

        st.divider()

        # MANAGE DEALS
        st.markdown("### Manage Deals")
        for deal in deals:
            with st.expander(f"{deal['address']} (Grade: {deal['grade']})"):
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**Price:** ${deal['price']:,.0f}")
                c2.write(f"**CoC:** {deal['coc']:.1f}%")
                if c3.button("Delete", key=f"del_{deal['id']}"):
                    try:
                        supabase.table("portfolios").delete().eq("id", deal['id']).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting: {e}")

        st.divider()

        # COMPARISON
        st.markdown("### Comparison Matrix")
        comp_df = pd.DataFrame(deals)
        # Rename columns to look nice
        comp_df = comp_df[['address', 'price', 'rent', 'coc', 'cashflow', 'grade']]
        comp_df.columns = ['Address', 'Price', 'Rent', 'CoC', 'Cashflow', 'Grade']

        def highlight_max(s):
            is_max = s == s.max()
            return ['background-color: #d1fae5; color: #065f46; font-weight: bold' if v else '' for v in is_max]

        st.dataframe(
            comp_df.style.format({
                "Price": "${:,.0f}",
                "Rent": "${:,.0f}",
                "CoC": "{:.1f}%",
                "Cashflow": "${:,.0f}"
            }).apply(highlight_max, subset=['CoC', 'Cashflow']),
            use_container_width=True
        )

        # CHARTS
        st.markdown("### Performance Visualizer")
        c1, c2 = st.columns(2)
        with c1:
            fig_coc = go.Figure(data=[go.Bar(x=comp_df['Address'], y=comp_df['CoC'], marker_color='#2563eb')])
            fig_coc.update_layout(title="Cash-on-Cash Return (%)", yaxis_title="CoC %")
            st.plotly_chart(fig_coc, use_container_width=True, config={'staticPlot': True})
        with c2:
            fig_cf = go.Figure(data=[go.Bar(x=comp_df['Address'], y=comp_df['Cashflow'], marker_color='#10b981')])
            fig_cf.update_layout(title="Monthly Cashflow ($)", yaxis_title="Cashflow $")
            st.plotly_chart(fig_cf, use_container_width=True, config={'staticPlot': True})

elif page == "IQ Center":
    # ==========================================
    # TAB 3: IQ CENTER
    # ==========================================
    st.header("YieldMap IQ Center: Expert Knowledge Base")
    st.markdown("---")

    st.subheader("1. Pro Metrics Explained")
    st.markdown(
        """
        * **Cash-on-Cash Return (CoC):** The most important metric for investors. It measures the annual net cash flow divided by your total cash investment (Down payment + Closing costs). A CoC of 12% is generally considered excellent.
        * **Net Monthly Cashflow:** The actual money left in your bank account each month after paying the Mortgage, Taxes, Insurance, Maintenance (Reserves), and Vacancy losses.
        * **Operating Expense Ratio (OER):** The percentage of your gross income that goes to operating expenses (excluding mortgage).
        """
    )
    st.markdown("---")

    st.subheader("2. Strategic Investment Grading")
    col_iq1, col_iq2 = st.columns(2)

    with col_iq1:
        st.markdown("#### Neighborhood Grades (Risk Profile)")
        st.caption("Based on FY 2026 Rent Ceilings (Income Proxy).")
        st.markdown(
            """
            * **Grade A (Prime / >$2500 Rent):** High appreciation, lower yield. Best for long-term hold.
            * **Grade B (Strong / $1800-$2500):** Balanced performance.
            * **Grade C (Stable / $1200-$1800):** The "Sweet Spot" for Section 8. High demand, solid yield.
            * **Grade D (Working / <$1200):** High cash flow potential but requires intensive management.
            """
        )

    with col_iq2:
        st.markdown("#### Deal Grades (Performance Index)")
        st.caption("Calculated using Cash-on-Cash Return.")
        st.markdown(
            """
            * **Grade A+ (Unicorn):** CoC > 12%. Immediate Buy.
            * **Grade B (Core Asset):** CoC 8-12%. Solid portfolio builder.
            * **Grade C (Average):** CoC < 8%. Average market return.
            * **Grade D (Distressed):** Negative cash flow or high risk.
            """
        )

    st.markdown("---")

    st.subheader("3. HUD & Utility Math Explained")
    col_iq3, col_iq4 = st.columns(2)

    with col_iq3:
        st.markdown("#### The 'Gross Rent' Trap")
        st.write("Many investors mistake the HUD FMR for their check amount. **HUD FMR includes utilities.**")
        st.info("**Net Contract Rent = HUD FMR - Utility Allowance**")
        st.markdown("If you miss this calculation, you could lose $150-$300/month in cash flow.")

        st.markdown("#### The 90-110% Rule (Voucher Standards)")
        st.warning("Did you know? The HUD FMR is just a baseline.")
        st.write("Local Housing Authorities (PHAs) can set their payments anywhere between **90% and 110%** of the HUD FMR. Some 'Opportunity Zones' pay up to 120%. Always call your local office to confirm their specific %.")

    with col_iq4:
        st.markdown("#### Utility Presets Guide")
        st.markdown(
            """
            * **Low ($120):** Modern Apartments, Gas Heat, Landlord pays Water/Sewer.
            * **Mid ($180):** Row Homes/Townhomes. Tenant pays Electric & Gas.
            * **High ($250):** Older Detached Homes, Oil/Electric Heat, Poor Insulation.
            """
        )
        st.caption("*Always download the specific UA Schedule from the local Housing Authority.*")

    st.markdown("---")

    st.subheader("4. Inspections & The 'Auto-Fail' List")
    st.write("Before you get paid, you must pass the HQS (Housing Quality Standards) Inspection. Here are the top failure items:")

    with st.expander("The Top 5 Inspection Failures (Check these first!)", expanded=True):
        st.markdown(
            """
            1.  **Peeling Paint:** If the home was built before 1978, *any* chipping or peeling paint (interior or exterior) is an automatic fail due to lead risk.
            2.  **Window Locks:** Every single window that is accessible from the outside (1st floor) must have a working lock.
            3.  **Water Heater TPR Valve:** The discharge pipe on the water heater must be copper/metal and end within 6 inches of the floor.
            4.  **Smoke & Carbon Detectors:** Must be present on every floor and in every bedroom.
            5.  **Trip Hazards:** Torn carpet, uneven concrete, or loose floorboards will fail.
            """
        )

    st.markdown("#### The 'Golden' Lease-Up Timeline")
    st.info("1. **Find Tenant** -> 2. **Submit RFTA (Request for Tenancy Approval)** -> 3. **Rent Determination** -> 4. **Inspection** -> 5. **Lease Sign** -> 6. **First Payment (can take 30-60 days)**")

    st.markdown("---")

    col_iq5, col_iq6 = st.columns(2)
    with col_iq5:
        st.subheader("5. The YieldMap Score")
        st.write("Our 100-point risk index is weighted as follows:")
        st.progress(40)
        st.caption("40% - HUD Rent Safety (Is the rent legal?)")
        st.progress(30)
        st.caption("30% - Gross Yield (Is the return high?)")
        st.progress(30)
        st.caption("30% - Absorption (Can we find a tenant?)")

    with col_iq6:
        st.subheader("6. Glossary of Terms")
        st.markdown(
            """
            * **FMR (Fair Market Rent):** HUD's gross rent limit for a county/zip.
            * **VPS (Voucher Payment Standard):** The actual amount the local PHA decides to pay (usually 90-110% of FMR).
            * **HAP Contract:** The contract between you and the PHA (Housing Authority).
            * **RFTA:** Request for Tenancy Approval (The 'packet' the tenant gives you).
            * **BRRRR:** Buy, Rehab, Rent, Refinance, Repeat. A strategy to pull capital out of a deal to buy the next one.
            """
        )

# INJECT THE TITAN BAR OVERLAY
st.markdown('<div class="titan-bar"></div>', unsafe_allow_html=True)

render_footer()

# === CRITICAL: Set Matplotlib Backend FIRST ===
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

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
import tempfile
import sys
import numpy as np
import io # Required for Excel buffer

# Try to import numpy_financial, fallback if missing
try:
    import numpy_financial as npf
except ImportError:
    npf = None

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
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
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

# --- HELPER: JAVASCRIPT REDIRECT ---
def js_redirect(url):
    redirect_code = f"""
    <script>
        window.top.location.href = "{url}";
    </script>
    <meta http-equiv="refresh" content="0;url={url}">
    """
    components.html(redirect_code, height=0, width=0)

# --- CRITICAL FIX: FORCE EMBED MODE (HIDES STREAMLIT BRANDING) ---
# This block checks if 'embed=true' is in the URL. If not, it reloads the page with it.
# This forces Streamlit to hide the "Manage App" button, Footer, and Header decoration.
if "embed" not in st.query_params:
    st.query_params["embed"] = "true"
    st.rerun()

# --- HANDLE EMAIL CONFIRMATION CODE ---
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        # Exchange code for session
        session = supabase.auth.exchange_code_for_session({"auth_code": code})
        st.session_state.user = session.user
        
        # Clear params but KEEP embed=true
        st.query_params.clear()
        st.query_params["embed"] = "true"
        st.rerun()
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

    /* 3. AGGRESSIVE HIDING (BACKUP FOR EMBED MODE) */
    header { visibility: hidden !important; height: 0px !important; }
    footer { visibility: hidden !important; display: none !important; height: 0px !important; }
    #MainMenu { visibility: hidden !important; display: none !important; }
    [data-testid="stToolbar"] { visibility: hidden !important; height: 0px !important; }
    [data-testid="manage-app-button"] { display: none !important; visibility: hidden !important; }
    .stAppDeployButton { display: none !important; visibility: hidden !important; }
    div[class^="viewerBadge"] { display: none !important; }
    
    /* 4. THE STICKY HEADER BACKGROUND */
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

    /* 5. BRANDING */
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

    /* 6. NAVIGATION BAR STYLING */
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

    /* 7. UNIVERSAL BUTTON STYLING */
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

    /* 8. CARDS & CONTAINERS */
    .stExpander, .element-container { border-radius: 8px; }
    h1, h2, h3, h4, h5 { color: #0f172a; font-weight: 700; letter-spacing: -0.025em; }

    /* 9. MOBILE RESPONSIVENESS */
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
    try:
        loan_amount = price * (1 - (down_payment_pct/100))
        if loan_amount <= 0: return 0
        if term_years <= 0: return loan_amount 
        monthly_rate = (interest_rate / 100) / 12
        num_payments = term_years * 12
        if monthly_rate == 0: return loan_amount / num_payments
        return loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    except: return 0

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

def calculate_projections(price, rent, total_expenses_yr, mortgage_yr, down_pct, interest_rate, term_years, rent_growth, appreciation, vacancy_rate):
    data = []
    # Gross rent starts here
    current_rent = rent * 12
    # Expenses usually grow, mortgage stays flat (unless ARM, but assuming fixed)
    current_expenses = total_expenses_yr
    loan_balance = price * (1 - down_pct/100)
    cumulative_cf = 0
    
    for year in range(1, 31):
        # 1. Apply Vacancy to Gross Rent
        effective_gross_income = current_rent * (1 - vacancy_rate/100)
        
        # 2. NOI
        noi = effective_gross_income - current_expenses
        
        # 3. Cash Flow
        cashflow = noi - mortgage_yr
        cumulative_cf += cashflow
        
        # 4. Loan Paydown
        if loan_balance > 0:
            interest_payment = loan_balance * (interest_rate/100)
            principal_payment = mortgage_yr - interest_payment
            if principal_payment > loan_balance: 
                principal_payment = loan_balance # Pay off remaining
            if principal_payment < 0:
                 principal_payment = 0 # Negative amortization protection
            loan_balance -= principal_payment
        
        # 5. Property Value
        property_value = price * ((1 + appreciation/100)**year)
        
        data.append({
            "Year": year, 
            "Cash Flow": cashflow, 
            "Cumulative CF": cumulative_cf,
            "Loan Balance": max(0, loan_balance), 
            "Total Equity": property_value - max(0, loan_balance),
            "Total Wealth Created": (property_value - max(0, loan_balance)) + cumulative_cf
        })
        
        # Grow Rent & Expenses for next year
        current_rent *= (1 + rent_growth/100)
        current_expenses *= (1 + rent_growth/100) # Simple expense growth assumption
        
    return pd.DataFrame(data)

# --- HYBRID IRR FUNCTION (Includes Reversion/Sale + Stability Fixes) ---
def calculate_irr(initial_investment, cash_flows, final_equity=0):
    """
    Calculates Internal Rate of Return (IRR).
    Correctly includes the property SALE (Reversion) at the end.
    Uses multi-guess approach to prevent OverflowError on negative deals.
    """
    # Create the full cash flow list: [-Investment, Year1, Year2, ... Year30 + Sale]
    values = [-initial_investment] + cash_flows
    
    # Add the sale proceeds (Equity) to the final year cash flow
    if values:
        values[-1] += final_equity
    
    # Check if we have valid inputs
    if not values: return 0.0

    # 1. Try Standard Library (Most Robust)
    if npf:
        try:
            val = npf.irr(values)
            return val * 100 if not math.isnan(val) else 0.0
        except:
            pass

    # 2. Manual Newton-Raphson method with Multi-Guess and Clamp
    def solve_irr(guess):
        for _ in range(100): # Max 100 iterations
            npv = 0
            d_npv = 0
            for t, val in enumerate(values):
                try:
                    denom = (1 + guess) ** t
                except OverflowError:
                    return None # Diverged
                
                if denom == 0: denom = 1e-9
                
                npv += val / denom
                try:
                    d_npv -= t * val / ((1 + guess) ** (t + 1))
                except OverflowError:
                    return None # Diverged
            
            if d_npv == 0:
                return None # Division by zero
            
            new_guess = guess - npv / d_npv
            
            # Clamp wild jumps
            if abs(new_guess - guess) > 1.0: 
                 new_guess = guess + 0.5 * np.sign(new_guess - guess)
            
            # Check convergence
            if abs(new_guess - guess) < 1e-6:
                return new_guess * 100
            
            guess = new_guess
            
            # Stop if out of reasonable bounds (-100% to 1000%)
            if abs(guess) > 10: return None
            
        return None

    # Try standard positive guess
    res = solve_irr(0.1)
    if res is not None: return res
    
    # Try negative guess (for loss scenarios)
    res = solve_irr(-0.1)
    if res is not None: return res
    
    # Try deep negative guess
    res = solve_irr(-0.5)
    if res is not None: return res
    
    return 0.0 # Failed to converge

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

# --- EXCEL GENERATOR FUNCTION (POWER MODE - XLSXWRITER ENABLED) ---
def generate_excel(address, market, unit, client, metrics_dict, inputs_dict, projections_df, expenses_dict, sensitivities):
    output = io.BytesIO()
    
    # Use xlsxwriter engine for advanced formatting
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Styles
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1e3a8a', 'font_color': '#ffffff', 'border': 1, 'align': 'center'})
        cell_fmt = workbook.add_format({'border': 1})
        money_fmt = workbook.add_format({'num_format': '$#,##0.00', 'border': 1})
        pct_fmt = workbook.add_format({'num_format': '0.0%', 'border': 1})
        red_fmt = workbook.add_format({'font_color': '#9C0006', 'bg_color': '#FFC7CE', 'num_format': '$#,##0.00', 'border': 1})
        
        # 1. SUMMARY SHEET
        summary_data = {
            "Metric": [
                "Property Address", "Market Area", "Unit Type", "Prepared For", 
                "Cash-on-Cash Return", "Monthly Cash Flow", "Cap Rate", "Op Expense Ratio",
                "Neighborhood Rating", "Deal Performance", "Max Allowable Offer",
                "Down Payment", "Closing Costs", "Repairs", "Total Cash Required", 
                "Break-Even Occupancy", "1.20x DSCR Price", "IRR (30yr)",
                "Analyst Insight"
            ],
            "Value": [
                address, market, unit, client,
                metrics_dict['coc']/100, metrics_dict['cf'], metrics_dict['cap']/100, metrics_dict['oer']/100,
                metrics_dict['n_grade'], metrics_dict['d_grade'], metrics_dict['mao'],
                metrics_dict['down_amt'], metrics_dict['closing_amt'], metrics_dict['repairs'], metrics_dict['total_cash'],
                metrics_dict['breakeven']/100, metrics_dict['dscr_price'], metrics_dict['irr']/100,
                "Calculated based on user inputs and federal data sources."
            ],
            "Notes": [
                "", "", "", "",
                "Annual CF / Total Cash", "Net Operating Income - Debt", "NOI / Purchase Price", "Op Ex / EGI",
                "Based on Rent Ceiling", "Based on CoC", "Target Price for 12% CoC",
                f"{inputs_dict['Down Payment']}%", f"{inputs_dict['Closing Costs']}%", "Estimate", "Down + Closing + Repairs",
                "Occupancy needed to cover costs", "Price to hit 1.20x Debt Coverage", "Internal Rate of Return",
                ""
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Format Summary
        ws_sum = writer.sheets['Summary']
        ws_sum.set_column('A:A', 30, cell_fmt)
        ws_sum.set_column('B:B', 20) 
        ws_sum.set_column('C:C', 40, cell_fmt)
        
        # Apply Formats to Value Column
        for i, val in enumerate(summary_data['Value']):
            row = i + 1
            if isinstance(val, (int, float)):
                if i == 4 and val < 0: # Conditional formatting for CoC < 0
                     ws_sum.write(row, 1, val, red_fmt)
                elif i in [4, 6, 7, 15, 17]: # Percentages
                    ws_sum.write(row, 1, val, pct_fmt)
                else: # Money
                    ws_sum.write(row, 1, val, money_fmt)
            else:
                ws_sum.write(row, 1, val, cell_fmt)

        # 2. VISUALS SHEET (EMBED CHARTS)
        ws_charts = workbook.add_worksheet('Visuals')
        
        # -- GENERATE PIE CHART IMAGE IN MEMORY --
        fig_pie = Figure(figsize=(5, 4))
        ax_pie = fig_pie.add_subplot(111)
        ax_pie.pie(list(expenses_dict.values()), labels=list(expenses_dict.keys()), autopct='%1.1f%%', startangle=90, colors=['#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8'])
        ax_pie.set_title("Monthly Expense Breakdown", fontsize=12, fontweight='bold')
        pie_buf = io.BytesIO()
        FigureCanvasAgg(fig_pie).print_png(pie_buf)
        pie_buf.seek(0)
        ws_charts.insert_image('A1', 'pie_chart.png', {'image_data': pie_buf})
        
        # -- GENERATE SENSITIVITY CHART IMAGE IN MEMORY --
        fig_sens = Figure(figsize=(6, 3))
        ax_sens = fig_sens.add_subplot(111)
        scenarios = ['Base', 'Rent+10%', 'Rent-10%', 'Rate-1%']
        s_vals = [
             sensitivities['base'], 
             sensitivities['rent_up'], 
             sensitivities['rent_down'], 
             sensitivities['rate_down']
        ]
        s_colors = ['#2563eb' if v >= 0 else '#ef4444' for v in s_vals]
        ax_sens.bar(scenarios, s_vals, color=s_colors)
        ax_sens.axhline(0, color='black', linewidth=0.8)
        ax_sens.set_title("Cash Flow Sensitivity ($/mo)", fontsize=10, fontweight='bold')
        ax_sens.grid(axis='y', alpha=0.3)
        sens_buf = io.BytesIO()
        FigureCanvasAgg(fig_sens).print_png(sens_buf)
        sens_buf.seek(0)
        ws_charts.insert_image('G1', 'sens_chart.png', {'image_data': sens_buf})

        # 2. PRO FORMA SHEET
        rent_val = inputs_dict.get('Rent', 0)
        
        # PRE-CALCULATE ANNUAL VALUES (Python Side) for Preview Accuracy
        # Monthly List
        monthly_vals = [
            rent_val, -expenses_dict['Vacancy'], rent_val - expenses_dict['Vacancy'],
            -expenses_dict['Taxes'], -expenses_dict['Insurance'], -expenses_dict['Maintenance'], -expenses_dict['Mgmt'],
            metrics_dict['noi'], -metrics_dict['mort'], metrics_dict['cf']
        ]
        # Annual List
        annual_vals = [val * 12 for val in monthly_vals]
        
        pro_forma_data = {
            "Category": ["Gross Market Rent", "Vacancy Loss", "Effective Gross Income", 
                         "Property Taxes", "Insurance", "Maintenance", "Property Mgmt", 
                         "Net Operating Income (NOI)", "Mortgage Payment", "Net Cash Flow"],
            "Monthly": monthly_vals,
            "Annual": annual_vals
        }
        df_pf = pd.DataFrame(pro_forma_data)
        df_pf.to_excel(writer, sheet_name='Pro Forma', index=False)
        
        ws_pf = writer.sheets['Pro Forma']
        ws_pf.set_column('A:A', 30, cell_fmt)
        ws_pf.set_column('B:B', 20, money_fmt)
        ws_pf.set_column('C:C', 20, money_fmt)
        
        # Add Header for Annual
        ws_pf.write(0, 2, "Annual", header_fmt)
        
        # Write Formulas for Annual Column (Live Calculation)
        # Fix: Start loop from row 1 (Excel row 2) to correct offset
        for i in range(len(pro_forma_data['Category'])):
            row_idx = i + 1 # Data starts at row index 1
            ws_pf.write_formula(row_idx, 2, f'=B{row_idx+1}*12', money_fmt)
            
        # 3. PROJECTIONS SHEET
        proj_export = projections_df[['Year', 'Cash Flow', 'Cumulative CF', 'Loan Balance', 'Total Equity', 'Total Wealth Created']]
        proj_export.to_excel(writer, sheet_name='Projections', index=False)
        
        ws_proj = writer.sheets['Projections']
        ws_proj.set_column('A:F', 18, money_fmt)
        
        # 4. SENSITIVITY SHEET
        sens_data = {
            "Scenario": ["Base Case", "Rent +10%", "Rent -10%", "Interest Rate -1%"],
            "Monthly Cash Flow": [sensitivities['base'], sensitivities['rent_up'], sensitivities['rent_down'], sensitivities['rate_down']]
        }
        pd.DataFrame(sens_data).to_excel(writer, sheet_name='Sensitivity', index=False)
        ws_sens = writer.sheets['Sensitivity']
        ws_sens.set_column('A:A', 25, cell_fmt)
        ws_sens.set_column('B:B', 20, money_fmt)
        
        # 5. INPUTS SHEET (Grouped)
        inputs_data = [
            {"Category": "ACQUISITION", "Parameter": "Purchase Price ($)", "Value": inputs_dict['Price']},
            {"Category": "", "Parameter": "Down Payment (%)", "Value": inputs_dict['Down Payment']/100},
            {"Category": "", "Parameter": "Closing Costs (%)", "Value": inputs_dict['Closing Costs']/100},
            {"Category": "", "Parameter": "Repairs ($)", "Value": inputs_dict['Repairs']},
            {"Category": "LOAN", "Parameter": "Interest Rate (%)", "Value": inputs_dict['Interest Rate']/100},
            {"Category": "", "Parameter": "Loan Term (Yrs)", "Value": inputs_dict['Term']},
            {"Category": "INCOME", "Parameter": "Gross Rent ($)", "Value": inputs_dict['Rent']},
            {"Category": "", "Parameter": "Vacancy Rate (%)", "Value": inputs_dict['Vacancy']/100},
            {"Category": "EXPENSES", "Parameter": "Property Taxes ($/yr)", "Value": inputs_dict['Taxes']},
            {"Category": "", "Parameter": "Insurance ($/yr)", "Value": inputs_dict['Insurance']},
            {"Category": "", "Parameter": "Maintenance (%)", "Value": inputs_dict['Maintenance']/100},
            {"Category": "", "Parameter": "Management (%)", "Value": inputs_dict['Mgmt']/100},
            {"Category": "GROWTH", "Parameter": "Appreciation (%)", "Value": inputs_dict['Appreciation']/100},
            {"Category": "", "Parameter": "Rent Growth (%)", "Value": inputs_dict['Rent Growth']/100}
        ]
        pd.DataFrame(inputs_data).to_excel(writer, sheet_name='Inputs', index=False)
        
        ws_inp = writer.sheets['Inputs']
        ws_inp.set_column('A:A', 20, cell_fmt)
        ws_inp.set_column('B:B', 30, cell_fmt)
        ws_inp.set_column('C:C', 15, cell_fmt)
        
        # 6. METADATA SHEET
        meta_data = {
            "Information": ["Generated By", "Date", "Data Source", "Disclaimer"],
            "Details": [
                "YieldMap Pro", 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "HUD FY 2026 Small Area FMRs",
                "Educational use only. Not financial advice."
            ]
        }
        pd.DataFrame(meta_data).to_excel(writer, sheet_name='Metadata', index=False)
        ws_meta = writer.sheets['Metadata']
        ws_meta.set_column('A:A', 20, cell_fmt)
        ws_meta.set_column('B:B', 50, cell_fmt)

    return output.getvalue()

# --- PDF GENERATOR CLASS ---
class ProPDF(FPDF):
    def __init__(self, user_logo=None):
        super().__init__()
        self.user_logo = user_logo

    def header(self):
        # LOGO LOGIC (White Label)
        if self.user_logo:
            # We must use a temp file because FPDF loads from path
            try:
                # Assuming user_logo is a file-like object from Streamlit or a path
                # If it's the temp path string passed from main function:
                _ = self.image(self.user_logo, 10, 8, 30) # Custom Logo
            except:
                pass # Fallback if image fails
        else:
            # Default YieldMap Header
            _ = self.set_fill_color(30, 58, 138)
            _ = self.rect(0, 0, 210, 30, 'F')
            _ = self.set_font('Helvetica', 'B', 24)
            _ = self.set_text_color(255, 255, 255)
            _ = self.set_xy(10, 8)
            _ = self.cell(0, 10, "YieldMap Pro", 0, 0, 'L')

        _ = self.set_font('Helvetica', '', 12)
        if self.user_logo:
             _ = self.set_text_color(100, 100, 100) # Darker text if white bg
        else:
             _ = self.set_text_color(147, 197, 253) # Lighter text if blue bg
             
        _ = self.set_xy(10, 18)
        _ = self.cell(0, 6, "SECTION 8 INTELLIGENCE REPORT", 0, 0, 'L')
        _ = self.set_font('Helvetica', 'B', 10)
        
        if self.user_logo:
             _ = self.set_text_color(50, 50, 50)
        else:
             _ = self.set_text_color(255, 255, 255)
             
        _ = self.set_xy(160, 10)
        _ = self.cell(40, 10, datetime.now().strftime('%Y-%m-%d'), 0, 0, 'R')
        _ = self.ln(25)

    def footer(self):
        _ = self.set_y(-15)
        _ = self.set_font('Helvetica', 'I', 8)
        _ = self.set_text_color(128, 128, 128)
        _ = self.cell(0, 10, f'YieldMap Pro | Generated for Pro Members | Page {self.page_no()} of {{nb}}', 0, 0, 'C')

    def check_space(self, height_needed):
        if self.get_y() + height_needed > 270:
            _ = self.add_page()

    def chapter_title(self, title):
        _ = self.ln(5)
        _ = self.set_font('Helvetica', 'B', 14)
        _ = self.set_text_color(30, 58, 138)
        _ = self.cell(0, 8, title, 0, 1, 'L')
        _ = self.set_draw_color(200, 200, 200)
        _ = self.line(10, self.get_y(), 200, self.get_y())
        _ = self.ln(4)

    def section_header(self, title):
        _ = self.ln(3)
        _ = self.set_font('Helvetica', 'B', 11)
        _ = self.set_text_color(50, 50, 50)
        _ = self.cell(0, 6, title, 0, 1, 'L')

    def kpi_box(self, label, value, x, y):
        _ = self.set_fill_color(248, 250, 252)
        _ = self.set_draw_color(200, 200, 200)
        _ = self.rect(x, y, 45, 25, 'DF')
        _ = self.set_xy(x, y + 5)
        _ = self.set_font('Helvetica', '', 9)
        _ = self.set_text_color(100, 100, 100)
        _ = self.cell(45, 5, label, 0, 0, 'C')
        _ = self.set_xy(x, y + 13)
        _ = self.set_font('Helvetica', 'B', 14)
        # Handle conditional formatting for negative values in PDF
        val_str = str(value)
        if "-" in val_str or "(" in val_str:
             _ = self.set_text_color(220, 38, 38)
        else:
             _ = self.set_text_color(30, 58, 138)
        _ = self.cell(45, 8, val_str, 0, 0, 'C')

    def add_row(self, col1, col2, is_total=False):
        _ = self.set_x(10)
        _ = self.set_font('Helvetica', 'B' if is_total else '', 10)
        fill = True if is_total else False
        _ = self.set_fill_color(240, 249, 255)
        
        # Conditional Red Text for Negatives
        if "-" in str(col2) or "(" in str(col2):
            _ = self.set_text_color(220, 38, 38) # Red
            _ = self.set_font('Helvetica', 'B', 10) # Bold
        else:
            _ = self.set_text_color(0, 0, 0) # Black
            
        _ = self.cell(140, 7, col1, 1, 0, 'L', fill)
        _ = self.cell(50, 7, col2, 1, 1, 'R', fill)
        
    def add_insight_box(self, text, is_good=True):
        _ = self.set_fill_color(240, 253, 244) if is_good else self.set_fill_color(254, 242, 242)
        _ = self.set_draw_color(22, 163, 74) if is_good else self.set_draw_color(220, 38, 38)
        _ = self.set_font('Helvetica', 'B', 10)
        text_width = self.get_string_width("ANALYST INSIGHT: " + text)
        
        # === FIX: Box height tripled to ensure text fit ===
        box_height = 20 if text_width > 180 else 15
        
        _ = self.rect(10, self.get_y(), 190, box_height, 'DF')
        _ = self.set_xy(12, self.get_y()+4)
        if is_good:
            _ = self.set_text_color(22, 101, 52)
        else:
            _ = self.set_text_color(153, 27, 27)
        _ = self.multi_cell(186, 6, "ANALYST INSIGHT: " + text, 0, 'L')
        _ = self.ln(box_height - 6)

def generate_chart_image(proj_df):
    # === GHOST TEXT FIX: Explicit Assignment to _ for ALL calls ===
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        fig = Figure(figsize=(7, 4))
        _ = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        
        _ = ax.fill_between(proj_df['Year'], 0, proj_df['Total Equity'], color='#1e3a8a', alpha=0.3, label='Equity')
        _ = ax.plot(proj_df['Year'], proj_df['Total Equity'], color='#1e3a8a', linewidth=2)
        _ = ax.plot(proj_df['Year'], proj_df['Loan Balance'], color='#ef4444', linestyle='--', label='Loan Balance')
        
        _ = ax.set_title("30-Year Equity Build-Up", fontsize=14, fontweight='bold')
        _ = ax.set_xlabel("Year")
        _ = ax.set_ylabel("Value ($)")
        _ = ax.legend()
        _ = ax.grid(True, alpha=0.3)
        
        _ = fig.tight_layout()
        _ = fig.savefig(tmpfile.name, dpi=100)
        
        return tmpfile.name

def generate_pie_chart(expenses):
    # Matplotlib Pie Chart for PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        fig = Figure(figsize=(5, 4))
        _ = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        
        labels = list(expenses.keys())
        values = list(expenses.values())
        
        _ = ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8'])
        _ = ax.set_title("Monthly Expense Breakdown", fontsize=12, fontweight='bold')
        
        _ = fig.tight_layout()
        _ = fig.savefig(tmpfile.name, dpi=100)
        return tmpfile.name

def generate_sensitivity_chart(base_cf, rent_up, rent_down, rate_up):
    # Matplotlib Bar Chart for Sensitivity
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        fig = Figure(figsize=(6, 3))
        _ = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        
        scenarios = ['Base Case', 'Rent +10%', 'Rent -10%', 'Rate +1%']
        values = [base_cf, rent_up, rent_down, rate_up]
        colors = ['#2563eb' if v >= 0 else '#ef4444' for v in values]
        
        _ = ax.bar(scenarios, values, color=colors)
        _ = ax.axhline(0, color='black', linewidth=0.8)
        _ = ax.set_title("Cash Flow Sensitivity ($/mo)", fontsize=10, fontweight='bold')
        _ = ax.grid(axis='y', alpha=0.3)
        
        _ = fig.tight_layout()
        _ = fig.savefig(tmpfile.name, dpi=100)
        return tmpfile.name

# === CRITICAL FIX: CACHE THE PDF GENERATION TO ISOLATE IT ===
@st.cache_data(show_spinner=False)
def generate_pro_report(client, address, row, unit, price, rent, v_rate, yield_val, coc_return, net_cashflow, d_grade, n_grade, down_pct, interest_rate, taxes, ins, maint_cost, loan_pmt, hud_limit, ua_val, maint_pct, pm_pct, term_years, repairs, projections_df, rent_growth, appreciation, closing_costs, mao, break_even_occ, price_120_dscr, report_notes, oer, irr, logo_path=None):
    # Pass logo path to class
    pdf = ProPDF(user_logo=logo_path)
    _ = pdf.alias_nb_pages()
    _ = pdf.add_page()
    
    # PAGE 1: EXECUTIVE SUMMARY
    _ = pdf.set_font('Helvetica', 'B', 16)
    _ = pdf.set_text_color(30, 58, 138)
    area_name = row.get('area_name', 'Unknown')
    _ = pdf.cell(0, 10, f"Analysis: {address}", 0, 1, 'L')
    _ = pdf.set_font('Helvetica', '', 10)
    _ = pdf.set_text_color(80, 80, 80)
    _ = pdf.cell(0, 5, f"Market Area: {area_name} | Unit Type: {unit}", 0, 1, 'L')
    _ = pdf.cell(0, 5, f"Prepared For: {client if client else 'Valued Client'}", 0, 1, 'L')
    _ = pdf.ln(5)

    # USER NOTES (If any)
    if report_notes:
        _ = pdf.set_fill_color(255, 255, 240) # Light yellow
        _ = pdf.set_text_color(50, 50, 50)
        _ = pdf.set_font('Helvetica', 'I', 9)
        _ = pdf.multi_cell(0, 6, f"Notes: {report_notes}", 1, 'L', True)
        _ = pdf.ln(5)
    
    total_wealth_30 = projections_df.iloc[-1]['Total Wealth Created'] # Updated to match table consistency
    if net_cashflow < 0:
        insight = f"Negative cash flow detected (-${abs(net_cashflow):,.2f}/mo). However, this asset builds ${total_wealth_30/1000:.0f}k in total wealth (Equity + CF) over 30 years."
        _ = pdf.add_insight_box(insight, is_good=False)
    elif coc_return > 12:
        insight = f"Excellent Performance! This deal exceeds the 12% CoC target and generates ${net_cashflow:,.2f}/mo in passive income."
        _ = pdf.add_insight_box(insight, is_good=True)
    else:
        insight = f"Stable Performance. This asset generates steady income and projects ${total_wealth_30/1000:.0f}k in long-term wealth creation."
        _ = pdf.add_insight_box(insight, is_good=True)

    y_kpi = pdf.get_y() + 5
    # Fix negative display for PDF KPI
    cf_display = f"(${abs(net_cashflow):,.2f})" if net_cashflow < 0 else f"${net_cashflow:,.2f}"
    
    _ = pdf.kpi_box("Cash-on-Cash", f"{coc_return:.1f}%", 10, y_kpi)
    _ = pdf.kpi_box("Monthly Flow", cf_display, 60, y_kpi)
    _ = pdf.kpi_box("Cap Rate", f"{yield_val:.1f}%", 110, y_kpi)
    
    # NEW: OER BOX
    _ = pdf.kpi_box("Op Expense Ratio", f"{oer:.1f}%", 160, y_kpi)
    _ = pdf.set_y(y_kpi + 35)

    _ = pdf.check_space(30)
    _ = pdf.chapter_title("Scorecard & Strategy")
    _ = pdf.set_font('Helvetica', '', 10)
    _ = pdf.cell(65, 8, f"Neighborhood Rating: {n_grade}", 1, 0, 'C')
    _ = pdf.cell(65, 8, f"Deal Performance: {d_grade}", 1, 0, 'C')
    _ = pdf.set_font('Helvetica', 'B', 10)
    _ = pdf.set_text_color(22, 101, 52)
    _ = pdf.cell(60, 8, f"Max Allowable Offer: ${mao:,.0f}", 1, 1, 'C') 
    _ = pdf.ln(10)

    _ = pdf.check_space(50)
    _ = pdf.chapter_title("Capital Requirements (Cash to Close)")
    down_amt = price * (down_pct / 100)
    closing_amt = price * (closing_costs / 100)
    total_cash = down_amt + closing_amt + repairs
    _ = pdf.add_row(f"Down Payment ({down_pct}%)", f"${down_amt:,.0f}")
    _ = pdf.add_row(f"Estimated Closing Costs ({closing_costs}%)", f"${closing_amt:,.0f}")
    _ = pdf.add_row("Immediate Repairs / HQS Prep", f"${repairs:,.0f}")
    _ = pdf.add_row("TOTAL CASH REQUIRED", f"${total_cash:,.0f}", True)

    _ = pdf.check_space(120)
    _ = pdf.chapter_title("Pro Forma Monthly Operating Statement")
    _ = pdf.section_header("Income")
    _ = pdf.add_row("Gross Market Rent (HUD FMR)", f"${rent:,.2f}")
    _ = pdf.add_row(f"Vacancy Allowance ({v_rate}%)", f"(${rent * (v_rate/100):,.2f})")
    _ = pdf.add_row("EFFECTIVE GROSS INCOME", f"${rent * (1 - v_rate/100):,.2f}", True)
    _ = pdf.section_header("Operating Expenses")
    _ = pdf.add_row("Property Taxes", f"(${taxes/12:,.2f})")
    _ = pdf.add_row("Insurance", f"(${ins/12:,.2f})")
    maint_monthly = maint_cost / 12
    _ = pdf.add_row(f"Maintenance Reserves ({maint_pct}%)", f"(${maint_monthly:,.2f})")
    _ = pdf.add_row(f"Property Management ({pm_pct}%)", f"(${rent * (pm_pct/100):,.2f})")
    noi_val = (rent * (1 - v_rate/100)) - (taxes/12 + ins/12 + maint_monthly + rent*(pm_pct/100))
    _ = pdf.add_row("NET OPERATING INCOME (NOI)", f"${noi_val:,.2f}", True)
    _ = pdf.check_space(30) 
    _ = pdf.section_header("Debt Service")
    # Fixed variable name here (int_rate -> interest_rate)
    _ = pdf.add_row(f"Mortgage Payment ({interest_rate}% @ {term_years}yrs)", f"(${loan_pmt:,.2f})")
    _ = pdf.ln(2)
    _ = pdf.set_fill_color(30, 58, 138)
    _ = pdf.set_text_color(255, 255, 255)
    _ = pdf.set_font('Helvetica', 'B', 12)
    _ = pdf.cell(140, 10, "ESTIMATED NET MONTHLY CASH FLOW", 1, 0, 'L', True)
    
    # Conditional formatting for final cashflow
    if net_cashflow < 0:
        _ = pdf.set_text_color(220, 38, 38) 
        _ = pdf.cell(50, 10, f"(${abs(net_cashflow):,.2f})", 1, 1, 'R', True)
    else:
        _ = pdf.set_text_color(22, 101, 52) # Green for positive!
        _ = pdf.cell(50, 10, f"${net_cashflow:,.2f}", 1, 1, 'R', True)

    # --- PAGE 2: BREAK-EVEN & CHARTS ---
    _ = pdf.add_page()
    _ = pdf.chapter_title("Break-Even & Risk Analysis")
    _ = pdf.add_row("Break-Even Occupancy", f"{break_even_occ:.1f}%")
    _ = pdf.add_row("Price for 1.20x DSCR", f"${price_120_dscr:,.0f}")
    # NEW: IRR ROW
    _ = pdf.add_row("30-Year Internal Rate of Return (IRR)", f"{irr:.2f}%")
    
    _ = pdf.ln(10)
    _ = pdf.chapter_title("Expense Breakdown")
    
    expenses_dict = {
        "Taxes": taxes/12,
        "Insurance": ins/12,
        "Maintenance": maint_monthly,
        "Mgmt": rent * (pm_pct/100),
        "Vacancy": rent * (v_rate/100)
    }
    pie_path = generate_pie_chart(expenses_dict)
    _ = pdf.image(pie_path, x=60, y=pdf.get_y(), w=90)
    _ = pdf.ln(95)
    _ = os.remove(pie_path)

    _ = pdf.chapter_title("Long-Term Wealth Projections")
    chart_path = generate_chart_image(projections_df)
    _ = pdf.image(chart_path, x=10, y=pdf.get_y(), w=190)
    _ = pdf.ln(95)
    _ = os.remove(chart_path)
    
    _ = pdf.set_fill_color(30, 58, 138)
    _ = pdf.set_text_color(255, 255, 255)
    _ = pdf.set_font('Helvetica', 'B', 9)
    _ = pdf.cell(18, 8, "Year", 1, 0, 'C', True)
    _ = pdf.cell(38, 8, "Annual CF", 1, 0, 'C', True)
    _ = pdf.cell(38, 8, "Loan Balance", 1, 0, 'C', True)
    _ = pdf.cell(38, 8, "Property Equity", 1, 0, 'C', True)
    _ = pdf.cell(56, 8, "Total Wealth Created", 1, 1, 'C', True)
    _ = pdf.set_text_color(50, 50, 50)
    _ = pdf.set_font('Helvetica', '', 9)
    
    snapshot_years = [1, 2, 3, 5, 7, 10, 15, 20, 30]
    cumulative_cf = 0
    for index, r in projections_df.iterrows():
        yr = int(r['Year'])
        cumulative_cf += r['Cash Flow']
        if yr in snapshot_years:
            if pdf.get_y() > 260:
                _ = pdf.add_page()
                _ = pdf.set_fill_color(30, 58, 138)
                _ = pdf.set_text_color(255, 255, 255)
                _ = pdf.set_font('Helvetica', 'B', 9)
                _ = pdf.cell(18, 8, "Year", 1, 0, 'C', True)
                _ = pdf.cell(38, 8, "Annual CF", 1, 0, 'C', True)
                _ = pdf.cell(38, 8, "Loan Balance", 1, 0, 'C', True)
                _ = pdf.cell(38, 8, "Property Equity", 1, 0, 'C', True)
                _ = pdf.cell(56, 8, "Total Wealth Created", 1, 1, 'C', True)
                _ = pdf.set_text_color(50, 50, 50)
                _ = pdf.set_font('Helvetica', '', 9)
            total_wealth = r['Total Equity'] + cumulative_cf - total_cash
            _ = pdf.set_x(10)
            _ = pdf.cell(18, 8, str(yr), 1, 0, 'C')
            
            # Format negative CF in red
            cf_val = r['Cash Flow']
            cf_str = f"${cf_val:,.0f}"
            if cf_val < 0:
                _ = pdf.set_text_color(220, 38, 38)
                cf_str = f"(${abs(cf_val):,.0f})"
            else:
                _ = pdf.set_text_color(50, 50, 50)
            _ = pdf.cell(38, 8, cf_str, 1, 0, 'C')
            
            _ = pdf.set_text_color(50, 50, 50) # Reset
            _ = pdf.cell(38, 8, f"${r['Loan Balance']:,.0f}", 1, 0, 'C')
            _ = pdf.cell(38, 8, f"${r['Total Equity']:,.0f}", 1, 0, 'C')
            _ = pdf.cell(56, 8, f"${total_wealth:,.0f}", 1, 1, 'C')

    _ = pdf.ln(10)
    _ = pdf.check_space(50)
    _ = pdf.chapter_title("Sensitivity Analysis (What-If)")
    
    rent_up = rent * 1.10
    rent_down = rent * 0.90
    rate_up = interest_rate + 1.0
    rate_down = interest_rate - 1.0
    def fast_cf(r, i):
        m = calculate_mortgage(price, down_pct, i, term_years)
        e = (taxes/12) + (ins/12) + (r * (maint_pct/100)) + (r * (pm_pct/100)) + (r * (v_rate/100))
        return (r - e - m)
    cf_base = net_cashflow
    cf_rent_up = fast_cf(rent_up, interest_rate)
    cf_rent_down = fast_cf(rent_down, interest_rate)
    cf_rate_down = fast_cf(rent, rate_down)
    cf_rate_up = fast_cf(rent, rate_up)
    
    _ = pdf.add_row("Base Case", f"${cf_base:,.0f}/mo")
    _ = pdf.add_row("Rent +10%", f"${cf_rent_up:,.0f}/mo")
    _ = pdf.add_row("Rent -10%", f"${cf_rent_down:,.0f}/mo")
    _ = pdf.add_row("Interest Rate -1%", f"${cf_rate_down:,.0f}/mo")
    
    _ = pdf.ln(5)
    # INCREASED BUFFER HERE TO 85mm
    sens_path = generate_sensitivity_chart(cf_base, cf_rent_up, cf_rent_down, cf_rate_up)
    _ = pdf.image(sens_path, x=10, y=pdf.get_y(), w=190)
    _ = pdf.ln(85) 
    _ = os.remove(sens_path)
    
    _ = pdf.ln(10)
    _ = pdf.set_font('Helvetica', 'B', 10)
    _ = pdf.cell(0, 6, "Analysis Assumptions:", 0, 1, 'L')
    _ = pdf.set_font('Helvetica', 'I', 8)
    _ = pdf.multi_cell(0, 5, f"Vacancy: {v_rate}% | Maint: {maint_pct}% | Mgmt: {pm_pct}% | Rent Growth: {rent_growth}% | Appreciation: {appreciation}% | Closing Costs: {closing_costs}%")
    _ = pdf.set_text_color(220, 38, 38)
    _ = pdf.multi_cell(0, 5, "** HUD FMRs are baselines. Local Housing Authorities (PHAs) determine final Voucher Payment Standards (VPS). Consult local PHA for overrides.")
    
    # === NEW: LEGAL DISCLAIMER ===
    _ = pdf.ln(10)
    _ = pdf.set_draw_color(100, 100, 100)
    _ = pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    _ = pdf.ln(2)
    _ = pdf.set_font('Helvetica', 'B', 8)
    _ = pdf.set_text_color(80, 80, 80)
    _ = pdf.cell(0, 5, "LEGAL & FINANCIAL DISCLAIMER", 0, 1, 'C')
    _ = pdf.set_font('Helvetica', '', 7)
    _ = pdf.set_text_color(100, 100, 100)
    disclaimer_text = (
        "This report is for educational and informational purposes only. "
        "YieldMap Pro is an analytical tool and does not constitute financial, legal, tax, or real estate investment advice. "
        "All calculations, projections, and grades are estimates based on user inputs and historical data. "
        "Actual results will vary. You should conduct your own independent due diligence and consult with qualified "
        "professionals (CPA, Attorney, Financial Advisor) before making any investment decisions. "
        "YieldMap Pro is not responsible for any financial losses or damages resulting from the use of this report."
    )
    _ = pdf.multi_cell(0, 4, disclaimer_text, 0, 'C')

    return pdf.output(dest='S').encode('latin-1')

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
# WRAP EVERYTHING IN MAIN() TO PREVENT GLOBAL SCOPE LEAKS
def main():
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

    # NEW: SUCCESS DIALOG (FIXED WITH STREAMLIT STATE BUTTON)
    @st.dialog("Account Created Successfully")
    def show_success_modal():
        st.write("Your account has been created.")
        st.write("Please check your email to confirm your address.")
        
        # === THE FIX: Use native Streamlit button logic ===
        if st.button("OK, Go to Login", type="primary", key="modal_ok_btn"):
            st.session_state.auth_mode = 'login'
            st.rerun()

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
                                
                                # *** NEW: REDIRECT ON LOGIN SUCCESS ***
                                js_redirect("https://yieldmappro.com/app?embed=true")
                                
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
        return

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
            
            # New: Report Notes Field
            report_notes = st.text_area("Report Notes (Optional)", placeholder="Add custom notes for the PDF cover page...", height=68)
            
            # New: Logo Upload (White Label)
            logo_file = st.file_uploader("Upload Your Logo (Optional)", type=['png', 'jpg', 'jpeg'], help="Customize the PDF report with your branding.")
            
            # Handle logo temp file
            logo_path = None
            if logo_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(logo_file.name)[1]) as tmp:
                    tmp.write(logo_file.getbuffer())
                    logo_path = tmp.name

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
                    _ = st_folium(m, height=350, use_container_width=True, returned_objects=[])  # Suppress return with _ and empty list
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
                    user_vacancy = st.number_input("Vacancy %", value=5.0, min_value=0.0, max_value=100.0, step=0.1, help="Estimated vacancy rate (5-8% typical)")
                    down_payment = st.number_input("Down %", value=20.0, min_value=0.0, max_value=100.0, step=1.0, help="Down payment percentage")
                    interest_rate = st.number_input("Rate %", value=7.0, min_value=0.0, max_value=20.0, step=0.1, help="Annual interest rate")
                    loan_term_years = st.number_input("Term", value=30, min_value=1, max_value=40, step=1, help="Loan term in years")
                    initial_repairs = st.number_input("Repairs", value=2000, min_value=0, step=100, help="Upfront repair costs")
                    appreciation = st.number_input("Appreciation %", value=2.0, min_value=0.0, max_value=20.0, step=0.1, help="Annual property appreciation rate")
                    rent_growth = st.number_input("Rent Growth %", value=2.0, min_value=0.0, max_value=20.0, step=0.1, help="Annual rent increase rate")
                with c2:
                    # Dynamic defaults based on Price
                    default_taxes = round(price * 0.012)
                    default_ins = round(price * 0.005)
                    taxes_yr = st.number_input("Taxes ($/yr)", value=default_taxes, min_value=0, help="Typical range: 0.8-1.2% of property value (e.g. Ontario ~1%)")
                    insurance_yr = st.number_input("Insurance ($/yr)", value=default_ins, min_value=0, help="Annual Insurance Premium (approx 0.5% of price)")
                    maint_capex = st.number_input("Maint/CapEx (%)", value=10.0, step=1.0, min_value=0.0, max_value=100.0, help="Maintenance & Capital Expenditures reserve")
                    prop_mgmt_pct = st.number_input("Mgmt %", value=8.0, min_value=0.0, max_value=100.0, step=1.0, help="Property Management fee")
                    closing_costs = st.number_input("Closing %", value=3.0, min_value=0.0, max_value=10.0, step=0.5, help="Closing costs percentage")
                    target_coc_input = st.number_input("Target CoC", value=12.0, min_value=0.0, max_value=100.0, step=0.5, help="Desired Cash-on-Cash Return")
                    
                # New: Rent Sensitivity Input (Text Box)
                st.markdown("---")
                st.markdown("##### Adjust Rent Percentage")
                rent_sens_pct = st.number_input("Adjust Rent (%)", value=0.0, step=1.0, help="Enter a percentage (e.g. 5.5, -2) to see instant cash flow impact.")
                
                # Live Calc for Sensitivity
                sens_rent = rent_in * (1 + rent_sens_pct/100)
                sens_gross = sens_rent * 12
                sens_vac = sens_gross * (user_vacancy/100)
                sens_egi = sens_gross - sens_vac
                sens_maint = sens_egi * (maint_capex/100)
                sens_pm = sens_gross * (prop_mgmt_pct/100)
                sens_opex = taxes_yr + insurance_yr + sens_maint + sens_pm
                sens_noi = sens_egi - sens_opex
                # Mortgage calc requires price/down/rate
                sens_mort = calculate_mortgage(price, down_payment, interest_rate, loan_term_years) * 12
                sens_cf = sens_noi - sens_mort
                
                # Calculate Base Investment
                base_invest = (price * down_payment / 100) + (price * closing_costs / 100) + initial_repairs
                
                # Calculate Sensitivity CoC
                sens_coc = (sens_cf * 12 / base_invest * 100) if base_invest > 0 else 0
                
                # Calculate Base Cash Flow for Delta
                base_cf = (rent_in*12 - (rent_in*12*user_vacancy/100) - (taxes_yr + insurance_yr + (rent_in*12*maint_capex/100) + (rent_in*12*prop_mgmt_pct/100)) - (calculate_mortgage(price, down_payment, interest_rate, loan_term_years)*12))/12
                
                # Display Sensitivity Result with New CoC
                s1, s2, s3 = st.columns(3)
                s1.metric("Adjusted Rent", f"${sens_rent:,.0f}")
                s2.metric("Est. Monthly CF", f"${sens_cf/12:,.2f}", delta=f"${(sens_cf/12 - base_cf/12):,.0f}", delta_color="normal")
                s3.metric("New CoC Return", f"{sens_coc:.1f}%", delta=None)


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
            
        # Corrected Cap Rate: NOI / Purchase Price
        cap_rate = (noi / price) * 100 if price > 0 else 0
        
        # OER Calculation
        oer = (exp / egi) * 100 if egi > 0 else 0

        # Break-Even Occupancy Calculation
        # Breakeven % = (Operating Expenses + Debt Service) / Gross Potential Rent
        total_annual_costs = exp + debt
        break_even_occupancy = (total_annual_costs / gross) * 100 if gross > 0 else 0
        
        # 1.20x DSCR Price Calculation
        monthly_rate = (interest_rate / 100) / 12
        num_payments = loan_term_years * 12
        if monthly_rate > 0:
            mortgage_constant = (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
            annual_debt_constant = mortgage_constant * 12
            ltv = 1 - (down_payment/100)
            target_max_debt = noi / 1.20 
            target_loan = target_max_debt / annual_debt_constant
            price_120_dscr = target_loan / ltv
        else:
            price_120_dscr = 0


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
        
        # Color code CoC
        coc_color = "normal" if coc > 0 else "inverse"
        r2.metric("CoC Return", f"{coc:.1f}%", delta=None, delta_color=coc_color)
        
        # Format CF with color and sign
        cf_val = cf / 12
        cf_display = f"${cf_val:,.2f}" # Changed to .2f for consistency
        if cf_val < 0:
            cf_color = "inverse"
        else:
            cf_color = "normal"
        r3.metric("Monthly CF", cf_display, delta=None, delta_color=cf_color)
        
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
            _ = st.plotly_chart(create_gauge(coc, "CoC %", 0, 20), use_container_width=True, config={'staticPlot': True})  # Suppress with _
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
            _ = st.plotly_chart(fig_eq, use_container_width=True, config={'staticPlot': True})  # Suppress with _
        
        st.divider()
        
        # OER and Break-Even Preview in App
        o1, o2 = st.columns(2)
        o1.metric("Op Expense Ratio (OER)", f"{oer:.1f}%", help="Operating Expenses / Effective Gross Income")
        o2.metric("Break-Even Occupancy", f"{break_even_occupancy:.1f}%", help="Occupancy % needed to cover all expenses and debt")

        st.divider()

        # Create Pie Chart (Donut) - STATIC (staticPlot=True)
        expense_labels = ['Taxes', 'Insurance', 'Maintenance', 'Property Mgmt', 'Vacancy Loss']
        expense_values = [taxes_yr/12, insurance_yr/12, maint/12, pm/12, vac_loss/12] # all monthly
        fig_pie = go.Figure(data=[go.Pie(labels=expense_labels, values=expense_values, hole=.4, hoverinfo="label+percent+value")])
        fig_pie.update_layout(title_text="Monthly Expense Breakdown", height=350, margin=dict(l=20, r=20, t=40, b=20))
        # STATIC AS REQUESTED
        _ = st.plotly_chart(fig_pie, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})

        st.divider()
        
        # --- MOVED CALCULATION LOGIC OUTSIDE THE COLUMN LAYOUT TO PREVENT GHOSTING ---
        with st.spinner("Processing..."):
            # Explicit assignment to prevent ghost text
            proj = calculate_projections(
                price,
                rent_in,
                exp,
                debt,
                down_payment,
                interest_rate,
                loan_term_years,
                rent_growth,
                appreciation,
                user_vacancy
            )
            
            # CALCULATE IRR
            # Correctly include Reversion (Sale Price at Year 30)
            final_year_equity = proj.iloc[-1]['Total Equity']
            irr_val = calculate_irr(invest, proj['Cash Flow'].tolist(), final_year_equity)

            # Generate Excel Data
            inputs_dict = {
                "Price": price, "Rent": rent_in, "Vacancy": user_vacancy, "Down Payment": down_payment,
                "Interest Rate": interest_rate, "Term": loan_term_years, "Repairs": initial_repairs,
                "Appreciation": appreciation, "Rent Growth": rent_growth, "Taxes": taxes_yr,
                "Insurance": insurance_yr, "Maintenance": maint_capex, "Mgmt": prop_mgmt_pct,
                "Closing Costs": closing_costs
            }
            metrics_dict = {
                "coc": coc, "cf": cf/12, "cap": cap_rate, "oer": oer, "n_grade": n_grade,
                "d_grade": d_grade, "mao": mao, "down_amt": price*down_payment/100,
                "closing_amt": price*closing_costs/100, "repairs": initial_repairs, "total_cash": invest,
                "breakeven": break_even_occupancy, "dscr_price": price_120_dscr, "irr": irr_val,
                "noi": noi/12, "mort": debt/12
            }
            expenses_dict = {
                "Vacancy": vac_loss/12, "Taxes": taxes_yr/12, "Insurance": insurance_yr/12,
                "Maintenance": maint/12, "Mgmt": pm/12
            }
            # Sensitivity Data for Excel
            def fast_cf_excel(r, i):
                m = calculate_mortgage(price, down_payment, i, loan_term_years)
                e = (taxes_yr/12) + (insurance_yr/12) + (r * (maint_capex/100)) + (r * (prop_mgmt_pct/100)) + (r * (user_vacancy/100))
                return (r - e - m)
            sensitivities = {
                "base": cf/12,
                "rent_up": fast_cf_excel(rent_in*1.1, interest_rate),
                "rent_down": fast_cf_excel(rent_in*0.9, interest_rate),
                "rate_down": fast_cf_excel(rent_in, interest_rate-1)
            }
            
            # Generate Files
            pdf_bytes = generate_pro_report(
                client_name, prop_address, row, beds, price, rent_in, user_vacancy, cap_rate, coc, 
                cf / 12, d_grade, n_grade, down_payment, interest_rate, taxes_yr, insurance_yr, 
                maint, mort, limit, ua_input, maint_capex, prop_mgmt_pct, loan_term_years, 
                initial_repairs, proj, rent_growth, appreciation, closing_costs, mao, 
                break_even_occupancy, price_120_dscr, report_notes, oer, irr_val, logo_path
            )
            
            excel_bytes = generate_excel(
                prop_address, market_area_name, beds, client_name, 
                metrics_dict, inputs_dict, proj, expenses_dict, sensitivities
            )

        # --- UI LAYOUT WITH BUTTONS ---
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
                    
                    # Set success message
                    st.success("Deal Saved to Portfolio! You can now download the files below.")
                    
                except Exception as e:
                    st.error(f"Error saving: {e}")

        # Construct filenames safely
        safe_addr = prop_address.strip() if prop_address else "Analysis"
        # Sanitize filename (remove slashes etc)
        safe_addr = "".join([c for c in safe_addr if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        
        pdf_name = f"YieldMap_{safe_addr}_{datetime.now().date()}.pdf"
        xlsx_name = f"YieldMap_{safe_addr}_{datetime.now().date()}.xlsx"

        with e2:
            st.download_button(
                "Download Report (PDF)",
                data=pdf_bytes,
                file_name=pdf_name,
                mime="application/pdf",
                use_container_width=True
            )

        with e3:
            st.download_button(
                "Export Data (Excel)",
                data=excel_bytes,
                file_name=xlsx_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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

            # NEW: BULK EXPORT BUTTON
            csv_export = pd.DataFrame(deals).to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Portfolio CSV",
                data=csv_export,
                file_name="My_Portfolio_YieldMap.csv",
                mime="text/csv",
                use_container_width=True
            )

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
                _ = st.plotly_chart(fig_coc, use_container_width=True, config={'staticPlot': True})  # Suppress with _ (for portfolio charts too)
            with c2:
                fig_cf = go.Figure(data=[go.Bar(x=comp_df['Address'], y=comp_df['Cashflow'], marker_color='#10b981')])
                fig_cf.update_layout(title="Monthly Cashflow ($)", yaxis_title="Cashflow $")
                _ = st.plotly_chart(fig_cf, use_container_width=True, config={'staticPlot': True})  # Suppress with _

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

# === CRITICAL: RUN MAIN APP ===
if __name__ == "__main__":
    main()

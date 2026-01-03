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

# --- 1. PRO CONFIGURATION ---
st.set_page_config(
    page_title="YieldMap Pro | Section 8 Intelligence",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. VISUAL UPGRADE: CUSTOM CSS (Aggressive Blue Button Override) ---
st.markdown(
    """
    <style>
    /* 1. GLOBAL FONT RESET */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #1e293b; /* Slate 800 */
    }

    /* 2. PUSH CONTENT DOWN */
    .block-container {
        padding-top: 7rem;
        padding-bottom: 5rem;
    }

    /* 3. HIDE DEFAULTS */
    header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    footer { visibility: hidden; }

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

    /* 5. BRANDING (Left Side) */
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

    /* Hide radio circles */
    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* Style nav links */
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

    div[role="radiogroup"] label:hover p {
        color: #ffffff !important;
    }

    div[role="radiogroup"] label[data-checked="true"] {
        background-color: rgba(255, 255, 255, 0.15) !important;
    }

    div[role="radiogroup"] label[data-checked="true"] p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* ============================================================ */
    /* 7.  FORCE ALL BUTTONS TO BE BLUE (THE FIX)                   */
    /* ============================================================ */

    /* A. Standard Buttons (Save Deal, etc.) */
    .stButton > button {
        background-color: #1e3a8a !important; 
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background-color: #1e40af !important;
        color: #ffffff !important;
    }

    /* B. Link Buttons (Zillow, Rentometer, PHA) */
    /* Streamlit renders these as <a> tags with specific test-ids */
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
    }
    /* Ensure the text inside the link button is white */
    a[data-testid="stLinkButton"] p {
        color: #ffffff !important;
    }
    /* Hover state for Link Buttons */
    a[data-testid="stLinkButton"]:hover {
        background-color: #1e40af !important;
        color: #ffffff !important;
        text-decoration: none !important;
    }

    /* C. Download Buttons (PDF, CSV) */
    .stDownloadButton > button {
        background-color: #1e3a8a !important; 
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button:hover {
        background-color: #1e40af !important;
        color: #ffffff !important;
    }
    .stDownloadButton > button:active, .stButton > button:active {
        background-color: #172554 !important;
        color: #ffffff !important;
    }

    /* ============================================================ */

    /* 9. CARDS & CONTAINERS */
    .stExpander, .element-container, [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        /* Clean look for containers */
    }
    
    /* Headers inside app */
    h1, h2, h3, h4, h5 {
        color: #0f172a;
        font-weight: 700;
        letter-spacing: -0.025em;
    }

    /* MOBILE RESPONSIVENESS */
    @media (max-width: 900px) {
        .brand-subtitle { display: none; }
        div[data-testid="stRadio"] {
            top: 80px;
            left: 0;
            width: 100%;
            background-color: #f1f5f9;
            padding: 10px;
            display: flex;
            justify-content: center;
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

# --- 3. REFERENCE DATA ---
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
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia"
}

# --- 4. DATA UTILITIES ---
@st.cache_data
def load_data():
    try:
        # Load HUD FY 2026 Data (Excel)
        df = pd.read_excel("hud_2026.xlsx", header=0, dtype=str)

        # CLEAN HEADERS
        df.columns = df.columns.astype(str).str.replace('\n', '_').str.replace(' ', '_').str.upper().str.strip()

        # REMOVE JUNK ROWS
        if 'ZIP_CODE' in df.columns:
            df = df.dropna(subset=['ZIP_CODE'])

        # RENAME COLUMNS
        rename_map = {
            'ZIP_CODE': 'zip_code',
            'ZIP': 'zip_code',
            'SAFMR_0BR': 'Studio',
            'SAFMR_1BR': '1-Bedroom',
            'SAFMR_2BR': '2-Bedroom',
            'SAFMR_3BR': '3-Bedroom',
            'SAFMR_4BR': '4-Bedroom',
            'HUD_FAIR_MARKET_RENT_AREA_NAME': 'area_name'
        }

        available_cols = []
        for c in rename_map.keys():
            if c in df.columns:
                available_cols.append(c)
        
        df = df[available_cols].rename(columns=rename_map)

        # EXTRACT STATE
        df['state_abbr'] = df['area_name'].str.extract(r',\s([A-Z]{2})')
        df['state'] = df['state_abbr'].map(STATE_MAP)
        df['state'] = df['state'].fillna('Other')

        # Convert Rent to Numeric
        cols_to_numeric = [
            'Studio',
            '1-Bedroom',
            '2-Bedroom',
            '3-Bedroom',
            '4-Bedroom'
        ]
        for c in cols_to_numeric:
            if c in df.columns:
                df[c] = pd.to_numeric(
                    df[c].str.replace('$', '').str.replace(',', ''),
                    errors='coerce'
                ).fillna(0)

        return df

    except Exception as e:
        st.error(f"CRITICAL ERROR loading data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=86400)
def get_vacancy_rate(zip_code):
    try:
        url_rate = f"https://api.census.gov/data/2023/acs/acs5/profile?get=DP04_0005PE&for=zip%20code%20tabulation%20area:{zip_code}"
        r = requests.get(url_rate, timeout=3)
        data = r.json()
        if len(data) > 1:
            if data[1][0]:
                return float(data[1][0])
    except:
        pass

    try:
        url_raw = f"https://api.census.gov/data/2023/acs/acs5?get=B25004_002E,B25003_003E&for=zip%20code%20tabulation%20area:{zip_code}"
        r = requests.get(url_raw, timeout=3)
        data = r.json()
        if len(data) > 1:
            vacant_for_rent = float(data[1][0])
            renter_occupied = float(data[1][1])
            total = vacant_for_rent + renter_occupied
            if total > 0:
                return round((vacant_for_rent / total) * 100, 1)
    except:
        pass
    return 5.0

# --- 5. MATH ENGINES ---
def calculate_mortgage(price, down_payment_pct, interest_rate, term_years=30):
    loan_amount = price * (1 - (down_payment_pct / 100))
    if loan_amount <= 0:
        return 0

    monthly_rate = (interest_rate / 100) / 12
    num_payments = term_years * 12

    if monthly_rate == 0:
        return loan_amount / num_payments

    return loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)

def calculate_max_offer(net_rent, target_coc, repairs, closing_costs_pct, down_pct, interest_rate, taxes, insurance, maint_monthly, pm_monthly):
    # Reverse calculates price based on target return
    test_price = 50000
    step = 1000

    for _ in range(1000):
        loan = test_price * (1 - down_pct / 100)
        monthly_pmt = calculate_mortgage(test_price, down_pct, interest_rate)

        cashflow_yr = (net_rent - (taxes / 12) - (insurance / 12) - maint_monthly - pm_monthly - monthly_pmt) * 12
        investment = (test_price * down_pct / 100) + (test_price * closing_costs_pct / 100) + repairs

        if investment > 0:
            coc = (cashflow_yr / investment) * 100
        else:
            coc = 0

        if coc < target_coc:
            return test_price - step

        test_price += step
    return 0

def calculate_projections(price, rent, total_expenses_yr, mortgage_yr, down_pct, interest_rate, term_years, rent_growth, appreciation):
    # Generates 30-year wealth chart data
    data = []
    current_rent = rent * 12
    current_expenses = total_expenses_yr
    loan_balance = price * (1 - down_pct / 100)

    for year in range(1, 31):
        # 1. Cash Flow
        noi = current_rent - current_expenses
        cashflow = noi - mortgage_yr

        # 2. Equity (Amortization)
        if loan_balance > 0:
            interest_payment = loan_balance * (interest_rate / 100)
            principal_payment = mortgage_yr - interest_payment
            if principal_payment > loan_balance:
                principal_payment = loan_balance
            loan_balance -= principal_payment

        # 3. Appreciation
        property_value = price * ((1 + appreciation / 100)**year)
        total_equity = property_value - loan_balance

        data.append({
            "Year": year,
            "Cash Flow": cashflow,
            "Loan Balance": loan_balance,
            "Total Equity": total_equity
        })

        # Inflate for next year
        current_rent *= (1 + rent_growth / 100)
        current_expenses *= (1 + rent_growth / 100)

    return pd.DataFrame(data)

# --- 6. MULTI-PAGE PDF GENERATOR ---
class ProPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 50)
        self.set_text_color(240, 240, 240)
        self.set_xy(0, 110)
        self.cell(210, 0, "YIELDMAP PRO", 0, 0, 'C')
        self.set_fill_color(37, 99, 235)
        self.set_xy(0, 0)
        self.rect(0, 0, 210, 22, 'F')

        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 6)
        self.cell(40, 10, "YieldMap", 0, 0, 'L')

        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(0, 6)
        self.cell(210, 10, "SECTION 8 ANALYSIS REPORT", 0, 0, 'C')

        self.set_font('Helvetica', '', 9)
        self.set_xy(160, 6)
        self.cell(40, 10, datetime.now().strftime('%Y-%m-%d'), 0, 0, 'R')
        self.ln(18)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'YieldMap Pro | Powered by HUD.gov | Page {self.page_no()} of {{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(37, 99, 235)
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def kpi_card(self, title, value, x, y, w=45, h=25):
        self.set_xy(x, y)
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(226, 232, 240)
        self.rect(x, y, w, h, 'DF')

        self.set_xy(x, y + 6)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(100, 116, 139)
        self.cell(w, 5, title, 0, 1, 'C')

        self.set_xy(x, y + 13)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(37, 99, 235)
        self.cell(w, 8, value, 0, 1, 'C')

    def add_table_row(self, label, value, fill=False, text_color=None):
        self.set_font('Helvetica', '', 10)
        self.set_fill_color(240, 253, 244)

        # Label Color
        self.set_text_color(50, 50, 50)
        self.cell(140, 8, label, 1, 0, 'L', fill)

        # Value Color Logic
        if text_color:
            self.set_text_color(*text_color)
        else:
            self.set_text_color(50, 50, 50)

        self.cell(50, 8, value, 1, 1, 'R', fill)
        self.set_text_color(50, 50, 50)

def generate_pro_report(client, address, row, unit, price, rent, v_rate, yield_val, coc_return, net_cashflow, d_grade, n_grade, down_pct, int_rate, taxes, ins, maint_cost, loan_pmt, hud_limit, ua_val, maint_pct, pm_pct, term_years, repairs, projections_df, rent_growth, appreciation, closing_costs):
    pdf = ProPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # EXECUTIVE SUMMARY
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    area_name = row.get('area_name', 'Unknown')
    pdf.multi_cell(0, 8, f"Property Analysis: {area_name}")
    pdf.ln(2)

    # Client Info Block
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(15, 6, "Client:", 0, 0, 'L')
    pdf.set_font('Helvetica', '', 10)
    
    client_text = client
    if not client_text:
        client_text = "Valued Investor"
    pdf.cell(80, 6, client_text, 0, 0, 'L')
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(15, 6, "Unit:", 0, 0, 'L')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(40, 6, unit, 0, 1, 'L')
    pdf.ln(6)
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(17, 6, "Address:", 0, 0, 'L')
    pdf.set_font('Helvetica', '', 10)
    
    address_text = address
    if not address_text:
        address_text = "Not Specified"
    pdf.cell(0, 6, address_text, 0, 1, 'L')
    pdf.ln(8)

    # KPI Grid
    y_start = pdf.get_y()
    pdf.kpi_card("Deal Grade", f"{d_grade}", 10, y_start)
    pdf.kpi_card("Cash-on-Cash", f"{coc_return:.2f}%", 60, y_start)
    pdf.kpi_card("Monthly Flow", f"${net_cashflow:,.0f}", 110, y_start)
    pdf.kpi_card("Cap Rate", f"{yield_val:.2f}%", 160, y_start)
    pdf.ln(32)

    # Disclaimer
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "*Deal Grade Logic: A+ (>12% CoC), B (8-12%), C (<8%). Based on conservative vacancy reserves.", 0, 1, 'L')
    pdf.ln(4)

    # FINANCIAL BREAKDOWN
    pdf.chapter_title("Financial Breakdown (Year 1)")
    pdf.add_table_row("Purchase Price", f"${price:,.0f}")
    pdf.add_table_row("HQS / Initial Repairs", f"${repairs:,.0f}")

    total_cash = (price * (down_pct / 100)) + (price * (closing_costs / 100)) + repairs
    pdf.add_table_row("Total Cash Needed (Inc. Closing)", f"${total_cash:,.0f}", True)
    pdf.add_table_row("Loan Amount", f"${price * (1 - down_pct / 100):,.0f}")
    pdf.add_table_row("Monthly P&I Payment", f"${loan_pmt:,.2f}")
    pdf.ln(5)

    # RENT & EXPENSES
    pdf.chapter_title("Section 8 Rent & Expenses")
    pdf.add_table_row("Gross HUD Rent", f"${rent:,.2f}")

    # Color Coded Risk
    if hud_limit > 0:
        pct_limit = (rent / hud_limit) * 100
        risk_color = (220, 20, 60) # Default Red
        if pct_limit <= 100:
            risk_color = (0, 128, 0) # Green

        risk_label = "Risk"
        if pct_limit <= 100:
            risk_label = "Safe"
            
        pdf.add_table_row(f"Rent vs. FMR ({pct_limit:.1f}% of Limit)", risk_label, False, risk_color)

    pdf.add_table_row(f"Vacancy Loss ({v_rate}%)", f"(${rent * (v_rate / 100):,.2f})")
    pdf.add_table_row("Effective Gross Income", f"${rent * (1 - v_rate / 100):,.2f}", True)
    pdf.add_table_row("Property Taxes", f"(${taxes / 12:,.2f})")
    pdf.add_table_row("Insurance", f"(${ins / 12:,.2f})")
    pdf.add_table_row(f"Maintenance & CapEx ({maint_pct}%)", f"(${maint_cost:,.2f})")
    pdf.add_table_row(f"Property Management ({pm_pct}%)", f"(${rent * (pm_pct / 100):,.2f})")
    
    noi_val = (rent * (1 - v_rate / 100)) - (taxes / 12 + ins / 12 + maint_cost + rent * (pm_pct / 100))
    pdf.add_table_row("Net Operating Income (NOI)", f"${noi_val:,.2f}", True)

    # PAGE 2: PROJECTIONS
    pdf.add_page()
    pdf.chapter_title("Buy & Hold Projections (Wealth Accumulation)")
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, f"This projection assumes a conservative {rent_growth}% annual rent increase and {appreciation}% appreciation. It demonstrates the power of loan paydown (Amortization) in Section 8 investing.")
    pdf.ln(5)

    # Table Header
    pdf.set_fill_color(37, 99, 235) # Blue
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(20, 8, "Year", 1, 0, 'C', True)
    pdf.cell(40, 8, "Cash Flow", 1, 0, 'C', True)
    pdf.cell(40, 8, "Loan Balance", 1, 0, 'C', True)
    pdf.cell(40, 8, "Total Equity", 1, 0, 'C', True)
    pdf.cell(40, 8, "Total Profit", 1, 1, 'C', True)

    # Table Rows
    pdf.set_text_color(50, 50, 50)
    pdf.set_font('Helvetica', '', 9)

    snapshot_years = [1, 2, 3, 5, 10, 20, 30]
    total_cf = 0
    initial_cash = (price * (down_pct / 100)) + (price * (closing_costs / 100)) + repairs

    for index, r in projections_df.iterrows():
        yr = int(r['Year'])
        total_cf += r['Cash Flow'] # Cumulative CF

        if yr in snapshot_years:
            pdf.cell(20, 8, f"Year {yr}", 1, 0, 'C')
            pdf.cell(40, 8, f"${r['Cash Flow']:,.0f}", 1, 0, 'C')
            pdf.cell(40, 8, f"${r['Loan Balance']:,.0f}", 1, 0, 'C')
            pdf.cell(40, 8, f"${r['Total Equity']:,.0f}", 1, 0, 'C')

            # Total Profit = Cumulative Cash Flow + Equity (minus initial investment)
            total_profit = total_cf + r['Total Equity'] - initial_cash
            pdf.cell(40, 8, f"${total_profit:,.0f}", 1, 1, 'C')

    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.multi_cell(0, 4, "Disclaimer: These projections are estimates based on your inputs. Past performance does not guarantee future results.")

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

# --- 8. MAIN APP ---
df = load_data()
if df.empty:
    st.error("DATABASE NOT FOUND: Please ensure 'hud_2026.xlsx' is uploaded.")
    st.stop()

# SESSION STATE INIT
if 'agreed' not in st.session_state:
    st.session_state.agreed = False
if 'pro_unlocked' not in st.session_state:
    st.session_state.pro_unlocked = False
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'scroll_to_top' not in st.session_state:
    st.session_state.scroll_to_top = False
if 'ua_value' not in st.session_state:
    st.session_state.ua_value = 150

# --- TERMS OF SERVICE SCREEN ---
if not st.session_state.agreed:
    st.title("🔒 YieldMap Pro")

    with st.expander("📝 READ FULL TERMS OF USE & PRIVACY POLICY", expanded=True):
        st.markdown(
            """
            ### **TERMS OF USE AND USER AGREEMENT**
            **Effective Date:** December 30, 2025 (FY 2026)

            **By clicking "Agree" or accessing the YieldMap Pro Application ("App"), you confirm you are at least 18 years old, eligible to use the service, and agree to these terms. If you disagree, do not use the App.**

            #### **1. NO FINANCIAL ADVICE**
            The YieldMap Pro Application ("App") is strictly an educational and analytical tool. Yieldmappro.com is **not** a registered investment advisor, broker-dealer, or financial institution. The data, scores, and grades provided are theoretical estimates and do not constitute financial advice. **The App is provided "as-is" and "as-available," without any warranties, express or implied.**

            #### **2. DATA ACCURACY & VERIFICATION**
            While we utilize official data from HUD and the U.S. Census Bureau, you acknowledge that:
            * HUD FMRs are subject to annual revision.
            * Utility Allowances vary by specific local Public Housing Authority (PHA) schedules.
            * **You are solely responsible** for verifying all rent limits and utility deductions with the local PHA before executing any contract.
            * We are not liable for third-party data errors, API downtime, or changes in government policies.

            #### **3. LIMITATION OF LIABILITY**
            In no event shall Yieldmappro.com, its owners, affiliates, or employees be liable for any direct, indirect, incidental, special, consequential, or punitive damages (including lost profits, data loss, or bad investment decisions) arising from your use of the App. **Our total liability is limited to the fees you paid us in the prior 12 months.**

            #### **4. PRIVACY POLICY & DATA USAGE**
            * **We DO NOT sell your data.** Any property data or underwriting assumptions you enter into this App are processed locally for the purpose of generating your session report.
            * We respect your privacy and will never monetize your personal usage habits or client lists.

            #### **5. INDEMNIFICATION**
            By accessing this App, you agree to indemnify, defend, and hold harmless Yieldmappro.com from any claims, losses, damages, liabilities, or expenses (including attorneys' fees) resulting from your use of the analytics, violation of these terms, or infringement of third-party rights.

            #### **6. INTELLECTUAL PROPERTY & USAGE RESTRICTIONS**
            All App content and algorithms are owned by Yieldmappro.com. You agree not to:
            * Copy, modify, or create derivative works.
            * Reverse-engineer or scrape the App.
            * **We may suspend access for violations without notice.**

            #### **7. GOVERNING LAW**
            These terms are governed by the laws of the United States. Any disputes will be resolved through binding arbitration.

            ---
            **Contact Us:** For questions, email support@yieldmappro.com.
            """
        )

    st.warning("⚠️ By checking the box below, you legally agree to these Terms.")

    # 1. THE CHECKBOX
    if st.checkbox("I have read and agree to the Terms of Use, Privacy Policy, and Limitation of Liability."):

        # 2. THE BUTTON
        if st.button("Accept & Enter Pro Analyzer"):
            st.session_state.agreed = True
            st.session_state.scroll_to_top = True
            st.rerun()

        # 3. AUTO-SCROLL DOWN
        st.markdown(
            """
            <script>
                setTimeout(function() {
                    var container = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
                    if (container) {
                        container.scrollTo({
                            top: container.scrollHeight, 
                            behavior: 'smooth'
                        });
                    }
                }, 300);
            </script>
            """,
            unsafe_allow_html=True
        )

    st.stop()

if st.session_state.get('scroll_to_top'):
    st.markdown(
        """
        <script>
            var body = window.parent.document.querySelector(".main");
            if (body) { body.scrollTop = 0; }
        </script>
        """,
        unsafe_allow_html=True
    )
    st.session_state.scroll_to_top = False

# --- HEADER SECTION (STICKY & BRANDED) ---
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

# --- NAVIGATION (HORIZONTAL RADIO BUTTONS) ---
# Visual logic moved to header via CSS.
page = st.radio(
    "Navigation",
    ["Pro Analyzer", "My Portfolio", "IQ Center"],
    horizontal=True,
    label_visibility="collapsed"
)

# --- MAIN CONTENT SWITCHER ---

if page == "Pro Analyzer":
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
        
        # UPDATE SESSION STATE FROM INPUT
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
        is_unlocked = st.session_state.pro_unlocked

        # ADVANCED CONFIG (SECTION STYLE, NO EMOJI)
        with st.container(border=True):
            st.markdown("##### Financial Assumptions")
            
            c1, c2 = st.columns(2)
            with c1:
                user_vacancy = st.number_input("Vacancy %", value=5.0, disabled=not is_unlocked)
                down_payment = st.number_input("Down %", value=20.0, disabled=not is_unlocked)
                interest_rate = st.number_input("Rate %", value=7.0, disabled=not is_unlocked)
                loan_term_years = st.number_input("Term", value=30, disabled=not is_unlocked)
                initial_repairs = st.number_input("Repairs", value=2000, disabled=not is_unlocked)
                appreciation = st.number_input("Appreciation %", value=2.0, disabled=not is_unlocked)
                rent_growth = st.number_input("Rent Growth %", value=2.0, disabled=not is_unlocked)
            with c2:
                taxes_yr = st.number_input("Taxes", value=3000, disabled=not is_unlocked)
                insurance_yr = st.number_input("Insurance", value=1200, disabled=not is_unlocked)
                
                # UPDATED: Maintenance is now a user input, not a slider
                maint_capex = st.number_input(
                    "Maint/CapEx (%)", 
                    value=10.0, 
                    step=1.0, 
                    disabled=not is_unlocked, 
                    help="Pro Only"
                )
                
                prop_mgmt_pct = st.number_input("Mgmt %", value=8.0, disabled=not is_unlocked)
                closing_costs = st.number_input("Closing %", value=3.0, disabled=not is_unlocked)
                target_coc_input = st.number_input("Target CoC", value=12.0, disabled=not is_unlocked)

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

    metric_grade = "🔒"
    if is_unlocked:
        metric_grade = d_grade
    r1.metric("Deal Grade", metric_grade)

    metric_coc = "🔒"
    if is_unlocked:
        metric_coc = f"{coc:.1f}%"
    r2.metric("CoC Return", metric_coc)

    metric_cf = "🔒"
    if is_unlocked:
        metric_cf = f"${cf / 12:,.0f}"
    r3.metric("Monthly CF", metric_cf)

    metric_invest = "🔒"
    if is_unlocked:
        metric_invest = f"${invest:,.0f}"
    r4.metric("Cash Needed", metric_invest)

    if is_unlocked:
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
    else:
        st.info("🔒 Unlock Pro for Max Offer")

    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        if is_unlocked:
            st.plotly_chart(create_gauge(coc, "CoC %", 0, 20), use_container_width=True)
        else:
            st.info("🔒 Gauge Locked")

    with g2:
        if is_unlocked:
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
            st.plotly_chart(fig_eq, use_container_width=True)
        else:
            st.info("🔒 Equity Locked")

    st.divider()

    # SECRET CODE CHECK
    try:
        PRO_CODE = st.secrets["PRO_CODE"]
    except:
        PRO_CODE = "1234"

    e1, e2, e3 = st.columns(3)

    with e1:
        if is_unlocked:
            if st.button("Save Deal", type="primary", use_container_width=True):
                save_address = prop_address
                if not save_address:
                    save_address = f"ZIP {selected_zip}"
                    
                st.session_state.portfolio.append({
                    "Address": save_address,
                    "Price": price,
                    "CoC": coc,
                    "Cashflow": cf / 12,
                    "Grade": d_grade
                })
                st.success("Saved!")
        else:
            c_input = st.text_input("Access Code", type="password")
            if c_input == PRO_CODE:
                st.session_state.pro_unlocked = True
                st.rerun()

    with e2:
        if is_unlocked:
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
    # TAB 2: PORTFOLIO
    # ==========================================
    st.header("Portfolio Command Center")
    if not st.session_state.portfolio:
        st.info("Your portfolio is empty. Go to the **Pro Analyzer** tab, run a deal, and click **'Save Deal'**.")
    else:
        # ANALYTICS SUMMARY
        t_cf = sum(d['Cashflow'] for d in st.session_state.portfolio)
        avg_c = sum(d['CoC'] for d in st.session_state.portfolio) / len(st.session_state.portfolio)
        t_val = sum(d['Price'] for d in st.session_state.portfolio)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total CF", f"${t_cf:,.0f}")
        c2.metric("Total Value", f"${t_val:,.0f}")
        c3.metric("Avg CoC", f"{avg_c:.1f}%")

        st.divider()

        # MANAGE DEALS
        st.markdown("### Manage Deals")
        for i, deal in enumerate(st.session_state.portfolio):
            with st.expander(f"{deal['Address']} (Grade: {deal['Grade']})"):
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**Price:** ${deal['Price']:,.0f}")
                c2.write(f"**CoC:** {deal['CoC']:.1f}%")
                if c3.button("Delete", key=f"port_del_{i}"):
                    st.session_state.portfolio.pop(i)
                    st.rerun()

        st.divider()

        # COMPARISON
        st.markdown("### Comparison Matrix")
        comp_df = pd.DataFrame(st.session_state.portfolio)

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

render_footer()
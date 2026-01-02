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
    page_title="YieldMap Pro",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 2. VISUAL UPGRADE: CUSTOM CSS (Sticky Header & Modern Fonts) ---
st.markdown("""
    <style>
    /* 1. GLOBAL FONT RESET */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* 2. PUSH CONTENT DOWN (So it doesn't hide behind the fixed header) */
    .block-container {
        padding-top: 6rem; 
        padding-bottom: 5rem;
    }
    
    /* 3. HIDE DEFAULT STREAMLIT JUNK */
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    footer {visibility: hidden;}
    
    /* 4. THE STICKY HEADER (SaaS Style) */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 70px;
        background-color: #1e3a8a; /* Deep Corporate Blue */
        z-index: 100000;
        display: flex;
        align-items: center;
        padding: 0 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    /* LOGO TEXT STYLING */
    .brand-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .brand-title {
        font-size: 24px;
        font-weight: 800; /* Bold */
        color: #ffffff;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1;
    }
    
    .brand-subtitle {
        font-size: 11px;
        font-weight: 400;
        color: #93c5fd; /* Soft Blue */
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 3px;
    }

    /* NAV LINKS (Visual Only - Decoration) */
    .header-nav {
        margin-left: 50px;
        display: flex;
        gap: 25px;
        font-size: 14px;
        font-weight: 500;
        color: rgba(255,255,255,0.8);
    }
    
    /* RESPONSIVE: Hide extra nav items on small screens */
    @media (max-width: 768px) {
        .header-nav { display: none; }
        .fixed-header { justify-content: center; }
        .brand-container { align-items: center; }
    }

    /* METRIC CARDS */
    [data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #1e3a8a !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
        color: #64748b !important;
    }
    
    /* INPUT FIELDS (Cards) */
    .stExpander, .element-container {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

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
            vacant_for_rent = float(data[1][0])
            renter_occupied = float(data[1][1])
            total = vacant_for_rent + renter_occupied
            if total > 0:
                return round((vacant_for_rent / total) * 100, 1)
    except: pass 
    return 5.0

# --- 5. MATH ENGINES ---
def calculate_mortgage(price, down_payment_pct, interest_rate, term_years=30):
    loan_amount = price * (1 - (down_payment_pct/100))
    if loan_amount <= 0: return 0
    monthly_rate = (interest_rate / 100) / 12
    num_payments = term_years * 12
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
        noi = current_rent - current_expenses
        cashflow = noi - mortgage_yr
        if loan_balance > 0:
            interest_payment = loan_balance * (interest_rate/100)
            principal_payment = mortgage_yr - interest_payment
            if principal_payment > loan_balance: principal_payment = loan_balance
            loan_balance -= principal_payment
        property_value = price * ((1 + appreciation/100)**year)
        data.append({"Year": year, "Cash Flow": cashflow, "Loan Balance": loan_balance, "Total Equity": property_value - loan_balance})
        current_rent *= (1 + rent_growth/100); current_expenses *= (1 + rent_growth/100)
    return pd.DataFrame(data)

# --- 6. MULTI-PAGE PDF GENERATOR ---
class ProPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 50); self.set_text_color(240, 240, 240)
        self.set_xy(0, 110); self.cell(210, 0, "YIELDMAP PRO", 0, 0, 'C')
        self.set_fill_color(37, 99, 235); self.set_xy(0,0); self.rect(0, 0, 210, 22, 'F')
        if os.path.exists("logo.png"): self.image("logo.png", 10, 4, 35) 
        else: self.set_font('Helvetica', 'B', 20); self.set_text_color(255, 255, 255); self.set_xy(10, 6); self.cell(40, 10, "YieldMap", 0, 0, 'L')
        self.set_font('Helvetica', 'B', 14); self.set_text_color(255, 255, 255)
        self.set_xy(0, 6); self.cell(210, 10, "SECTION 8 ANALYSIS REPORT", 0, 0, 'C')
        self.set_font('Helvetica', '', 9); self.set_xy(160, 6); self.cell(40, 10, datetime.now().strftime('%Y-%m-%d'), 0, 0, 'R')
        self.ln(18)
    def footer(self):
        self.set_y(-15); self.set_font('Helvetica', 'I', 8); self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'YieldMap Pro | Powered by HUD.gov | Page {self.page_no()} of {{nb}}', 0, 0, 'C')
    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 12); self.set_text_color(37, 99, 235)
        self.cell(0, 10, title, 0, 1, 'L'); self.set_draw_color(200, 200, 200); self.line(10, self.get_y(), 200, self.get_y()); self.ln(2)
    def kpi_card(self, title, value, x, y, w=45, h=25):
        self.set_xy(x, y); self.set_fill_color(248, 250, 252); self.set_draw_color(226, 232, 240); self.rect(x, y, w, h, 'DF')
        self.set_xy(x, y+6); self.set_font('Helvetica', 'B', 9); self.set_text_color(100, 116, 139); self.cell(w, 5, title, 0, 1, 'C')
        self.set_xy(x, y+13); self.set_font('Helvetica', 'B', 14); self.set_text_color(37, 99, 235); self.cell(w, 8, value, 0, 1, 'C')
    
    def add_table_row(self, label, value, fill=False, text_color=None):
        self.set_font('Helvetica', '', 10); self.set_fill_color(240, 253, 244)
        if text_color: self.set_text_color(*text_color)
        else: self.set_text_color(50, 50, 50)
        self.cell(140, 8, label, 1, 0, 'L', fill); self.cell(50, 8, value, 1, 1, 'R', fill)
        self.set_text_color(50, 50, 50)

def generate_pro_report(client, address, row, unit, price, rent, v_rate, yield_val, coc_return, net_cashflow, d_grade, n_grade, down_pct, int_rate, taxes, ins, maint_cost, loan_pmt, hud_limit, ua_val, maint_pct, pm_pct, term_years, repairs, projections_df, rent_growth, appreciation, closing_costs):
    pdf = ProPDF(); pdf.alias_nb_pages(); pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16); pdf.set_text_color(30, 41, 59)
    area_name = row.get('area_name', 'Unknown'); pdf.multi_cell(0, 8, f"Property Analysis: {area_name}"); pdf.ln(2)
    pdf.set_x(10); pdf.set_font('Helvetica', 'B', 10); pdf.set_text_color(100, 100, 100)
    pdf.cell(15, 6, "Client:", 0, 0, 'L'); pdf.set_font('Helvetica', '', 10); pdf.cell(80, 6, client or "Valued Investor", 0, 0, 'L') 
    pdf.set_font('Helvetica', 'B', 10); pdf.cell(15, 6, "Unit:", 0, 0, 'L'); pdf.set_font('Helvetica', '', 10); pdf.cell(40, 6, unit, 0, 1, 'L'); pdf.ln(6)
    pdf.set_font('Helvetica', 'B', 10); pdf.cell(17, 6, "Address:", 0, 0, 'L'); pdf.set_font('Helvetica', '', 10); pdf.cell(0, 6, address or "Not Specified", 0, 1, 'L'); pdf.ln(8)
    y_start = pdf.get_y(); pdf.kpi_card("Deal Grade", f"{d_grade}", 10, y_start); pdf.kpi_card("Cash-on-Cash", f"{coc_return:.2f}%", 60, y_start)
    pdf.kpi_card("Monthly Flow", f"${net_cashflow:,.0f}", 110, y_start); pdf.kpi_card("Cap Rate", f"{yield_val:.2f}%", 160, y_start); pdf.ln(32)
    pdf.set_font('Helvetica', 'I', 8); pdf.set_text_color(100, 100, 100); pdf.cell(0, 5, "*Deal Grade Logic: A+ (>12% CoC), B (8-12%), C (<8%).", 0, 1, 'L'); pdf.ln(4)
    
    pdf.chapter_title("Financial Breakdown (Year 1)")
    pdf.add_table_row("Purchase Price", f"${price:,.0f}")
    pdf.add_table_row("HQS / Initial Repairs", f"${repairs:,.0f}")
    total_cash = (price*(down_pct/100)) + (price*(closing_costs/100)) + repairs
    pdf.add_table_row("Total Cash Needed (Inc. Closing)", f"${total_cash:,.0f}", True)
    pdf.add_table_row("Loan Amount", f"${price*(1-down_pct/100):,.0f}")
    pdf.add_table_row("Monthly P&I Payment", f"${loan_pmt:,.2f}")
    pdf.ln(5)
    
    pdf.chapter_title("Section 8 Rent & Expenses")
    pdf.add_table_row("Gross HUD Rent", f"${rent:,.2f}")
    if hud_limit > 0:
        pct_limit = (rent / hud_limit) * 100
        risk_color = (0, 128, 0) if pct_limit <= 100 else (220, 20, 60)
        pdf.add_table_row(f"Rent vs. FMR ({pct_limit:.1f}% of Limit)", f"{'Safe' if pct_limit <= 100 else 'Risk'}", False, risk_color)
    pdf.add_table_row(f"Vacancy Loss ({v_rate}%)", f"(${rent * (v_rate/100):,.2f})")
    pdf.add_table_row("Effective Gross Income", f"${rent * (1 - v_rate/100):,.2f}", True)
    pdf.add_table_row("Property Taxes", f"(${taxes/12:,.2f})")
    pdf.add_table_row("Insurance", f"(${ins/12:,.2f})")
    pdf.add_table_row(f"Maintenance & CapEx ({maint_pct}%)", f"(${maint_cost:,.2f})")
    pdf.add_table_row(f"Property Management ({pm_pct}%)", f"(${rent * (pm_pct/100):,.2f})")
    pdf.add_table_row("Net Operating Income (NOI)", f"${(rent * (1 - v_rate/100)) - (taxes/12 + ins/12 + maint_cost + rent*(pm_pct/100)):,.2f}", True)
    
    pdf.add_page(); pdf.chapter_title("Buy & Hold Projections (Wealth Accumulation)"); 
    pdf.set_font('Helvetica', '', 9); 
    pdf.multi_cell(0, 5, f"This projection assumes a conservative {rent_growth}% annual rent increase and {appreciation}% appreciation.")
    pdf.ln(5); pdf.set_fill_color(37, 99, 235); pdf.set_text_color(255, 255, 255); pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(20, 8, "Year", 1, 0, 'C', True); pdf.cell(40, 8, "Cash Flow", 1, 0, 'C', True); pdf.cell(40, 8, "Loan Balance", 1, 0, 'C', True)
    pdf.cell(40, 8, "Total Equity", 1, 0, 'C', True); pdf.cell(40, 8, "Total Profit", 1, 1, 'C', True); pdf.set_text_color(50, 50, 50); pdf.set_font('Helvetica', '', 9)
    snapshot_years = [1, 2, 3, 5, 10, 20, 30]; total_cf = 0; initial_cash = (price*(down_pct/100)) + (price*(closing_costs/100)) + repairs
    for index, r in projections_df.iterrows():
        yr = int(r['Year']); total_cf += r['Cash Flow']
        if yr in snapshot_years:
            pdf.cell(20, 8, f"Year {yr}", 1, 0, 'C'); pdf.cell(40, 8, f"${r['Cash Flow']:,.0f}", 1, 0, 'C'); pdf.cell(40, 8, f"${r['Loan Balance']:,.0f}", 1, 0, 'C')
            pdf.cell(40, 8, f"${r['Total Equity']:,.0f}", 1, 0, 'C'); pdf.cell(40, 8, f"${total_cf + r['Total Equity'] - initial_cash:,.0f}", 1, 1, 'C')
    pdf.ln(10); pdf.set_font('Helvetica', 'I', 8); pdf.multi_cell(0, 4, "Disclaimer: Estimates only.")
    return pdf.output(dest='S')

def create_gauge(value, title, min_v, max_v, suffix="%", flip=False):
    colors = ["#fee2e2", "#fef3c7", "#d1fae5"] if not flip else ["#d1fae5", "#fef3c7", "#fee2e2"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, number={'suffix': suffix, 'font': {'size': 35}},
        gauge={'axis': {'range': [min_v, max_v]}, 'bar': {'color': "#2563eb"},
               'steps': [{'range': [min_v, max_v*0.33], 'color': colors[0]},
                         {'range': [max_v*0.33, max_v*0.66], 'color': colors[1]},
                         {'range': [max_v*0.66, max_v], 'color': colors[2]}]}))
    fig.update_layout(height=180, margin=dict(l=40, r=40, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig

def render_footer():
    st.divider(); st.markdown("""<div style="text-align: center; font-size: 12px; color: #64748b;"><p><strong>Yieldmappro.com</strong> | © 2025 All Rights Reserved</p></div>""", unsafe_allow_html=True)

# --- 8. MAIN APP ---
df = load_data()
if df.empty: st.error("DATABASE NOT FOUND"); st.stop()

if 'agreed' not in st.session_state: st.session_state.agreed = False
if 'pro_unlocked' not in st.session_state: st.session_state.pro_unlocked = False
if 'portfolio' not in st.session_state: st.session_state.portfolio = []

if not st.session_state.agreed:
    st.title("🔒 YieldMap Pro")
    with st.expander("📝 TERMS OF USE", expanded=True):
        st.markdown("### Terms: No Financial Advice. Use at Own Risk.")
    if st.checkbox("I Agree"):
        if st.button("Enter Pro Analyzer"): st.session_state.agreed = True; st.rerun()
    st.stop()

# --- HEADER SECTION (STICKY & BRANDED) ---
st.markdown("""
    <div class="fixed-header">
        <div class="brand-container">
            <div class="brand-title">YieldMap Pro</div>
            <div class="brand-subtitle">Section 8 Intelligence • FY 2026</div>
        </div>
        <div class="header-nav">
            <span>Market Analysis</span>
            <span>Portfolio</span>
            <span>Strategy</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- MAIN TABS ---
tab_anal, tab_port, tab_iq = st.tabs(["📊 Pro Analyzer", "📁 My Portfolio", "📖 IQ Center"])

with tab_anal:
    with st.container(border=True):
        st.markdown("#### 1. Property Details")
        c1, c2 = st.columns(2)
        with c1: client_name = st.text_input("Client", placeholder="Client Name")
        with c2: prop_address = st.text_input("Address", placeholder="123 Main St")
        
        c1, c2, c3 = st.columns(3)
        with c1: selected_state = st.selectbox("State", sorted([s for s in df['state'].unique() if s != 'Other']))
        with c2: selected_zip = st.selectbox("ZIP", sorted(df[df['state'] == selected_state]['zip_code'].unique()))
        with c3: beds = st.selectbox("Unit", ["Studio", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom"], index=2)

    row = df[df['zip_code'] == selected_zip].iloc[0]
    market_area_name = row.get('area_name', 'Unknown Area')

    st.markdown("---")
    st.markdown(f"#### 📍 {market_area_name} ({selected_zip})")
    
    # SMART LINKS
    c1, c2, c3 = st.columns(3)
    zillow_url = f"https://www.zillow.com/homes/for_rent/{selected_zip}_rb/{beds.split('-')[0]}_beds/"
    rentometer_url = "https://www.rentometer.com/"
    pha_url = "https://www.hud.gov/program_offices/public_indian_housing/pha/contacts"
    with c1: st.link_button("🏠 Zillow Comps", zillow_url, use_container_width=True)
    with c2: st.link_button("📊 Rentometer", rentometer_url, use_container_width=True)
    with c3: st.link_button("🏛️ Find PHA", pha_url, use_container_width=True)

    try:
        import pgeocode; import folium; from streamlit_folium import st_folium
        nomi = pgeocode.Nominatim('us')
        loc = nomi.query_postal_code(selected_zip)
        if not math.isnan(loc.latitude):
            m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=13)
            folium.Marker([loc.latitude, loc.longitude], icon=folium.Icon(color="blue", icon="home", prefix='fa')).add_to(m)
            st_folium(m, height=350, use_container_width=True)
    except: pass

    st.markdown("---")
    limit = row[beds]
    with st.container(border=True):
        st.markdown(f"#### ⚡ Pro Underwriting")
        c1, c2 = st.columns([2,1])
        with c1: ua_input = st.slider("Utility Allowance", 0, 400, 150)
        target_rent = limit - ua_input
        with c2: st.info(f"**HUD Limit:** ${limit:,.0f}\n\n**Net Rent:** ${target_rent:,.0f}")

    with st.container(border=True):
        st.markdown("#### Acquisition")
        c1, c2 = st.columns(2)
        with c1: price = st.number_input("Price", value=250000)
        with c2: rent_in = st.number_input("Rent", value=int(target_rent))
        
        api_vacancy = get_vacancy_rate(selected_zip)
        is_unlocked = st.session_state.pro_unlocked
        
        with st.expander("⚙️ Advanced Config & API Keys (Pro)", expanded=True):
            # API CONFIG IS HERE NOW (Replaces gear button)
            st.caption("System Configuration")
            api_input = st.text_input("RentCast API Key", type="password", help="Optional")
            st.divider()
            
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
                maint_capex = st.slider("Maint %", 0, 20, 10, disabled=not is_unlocked)
                prop_mgmt_pct = st.number_input("Mgmt %", value=8.0, disabled=not is_unlocked)
                closing_costs = st.number_input("Closing %", value=3.0, disabled=not is_unlocked)
                target_coc_input = st.number_input("Target CoC", value=12.0, disabled=not is_unlocked)

    # CALCS
    gross = rent_in * 12
    vac_loss = gross * (user_vacancy/100)
    egi = gross - vac_loss
    maint = egi * (maint_capex/100)
    pm = gross * (prop_mgmt_pct/100)
    exp = taxes_yr + insurance_yr + maint + pm
    noi = egi - exp
    mort = calculate_mortgage(price, down_payment, interest_rate, loan_term_years)
    debt = mort * 12
    cf = noi - debt
    invest = (price * down_payment/100) + (price * closing_costs/100) + initial_repairs
    coc = (cf / invest * 100) if invest > 0 else 0
    
    if limit >= 2500: n_grade = "A"
    elif limit >= 1800: n_grade = "B"
    else: n_grade = "C"
    
    if coc >= 12: d_grade = "A+"
    elif coc >= 8: d_grade = "B"
    else: d_grade = "C"

    st.divider()
    if os.path.exists("logo.png"):
        logo_b64 = base64.b64encode(open("logo.png", "rb").read()).decode()
        st.markdown(f'<div class="rating-title"><img src="data:image/png;base64,{logo_b64}" width="60"><h2 class="rating-text">YieldMap Asset Rating</h2></div>', unsafe_allow_html=True)
    else: st.markdown("## YieldMap Asset Rating")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Deal Grade", d_grade if is_unlocked else "🔒")
    r2.metric("CoC Return", f"{coc:.1f}%" if is_unlocked else "🔒")
    r3.metric("Monthly CF", f"${cf/12:,.0f}" if is_unlocked else "🔒")
    r4.metric("Cash Needed", f"${invest:,.0f}" if is_unlocked else "🔒")

    if is_unlocked:
        mao = calculate_max_offer(rent_in*(1-user_vacancy/100), target_coc_input, initial_repairs, closing_costs, down_payment, interest_rate, taxes_yr, insurance_yr, maint/12, pm/12)
        st.info(f"🎯 **MAO:** ${mao:,.0f} for {target_coc_input}% CoC")
    else: st.info("🔒 Unlock Pro for Max Offer")

    st.divider()
    g1, g2 = st.columns(2)
    with g1: 
        if is_unlocked:
            st.plotly_chart(create_gauge(coc, "CoC %", 0, 20), use_container_width=True)
        else: st.info("🔒 Gauge Locked")
    with g2:
        if is_unlocked:
            years = list(range(1, 6)); equity_vals = []; current_bal = price * (1 - down_payment/100)
            for y in years:
                paid_principal = (mort * 12) - (current_bal * interest_rate/100)
                if paid_principal < 0: paid_principal = 0 
                current_bal -= paid_principal
                equity = price * ((1 + appreciation/100)**y) - current_bal
                equity_vals.append(equity)
            fig_eq = go.Figure(); fig_eq.add_trace(go.Scatter(x=years, y=equity_vals, fill='tozeroy'))
            fig_eq.update_layout(height=180, margin=dict(l=20,r=20,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_eq, use_container_width=True)
        else: st.info("🔒 Equity Locked")

    st.divider()
    try: PRO_CODE = st.secrets["PRO_CODE"]
    except: PRO_CODE = "1234"
    e1, e2, e3 = st.columns(3)
    
    with e1:
        if is_unlocked:
            if st.button("💾 Save", type="primary", use_container_width=True):
                st.session_state.portfolio.append({"Address": prop_address, "Price": price, "CoC": coc, "Cashflow": cf/12, "Grade": d_grade})
                st.success("Saved!")
        else:
            c_input = st.text_input("Access Code", type="password")
            if c_input == PRO_CODE: st.session_state.pro_unlocked = True; st.rerun()
            
    with e2:
        if is_unlocked:
            proj = calculate_projections(price, rent_in, exp, debt, down_payment, interest_rate, loan_term_years, rent_growth, appreciation)
            pdf = generate_pro_report(client_name, prop_address, row, beds, price, rent_in, user_vacancy, 0, coc, cf/12, d_grade, n_grade, down_payment, interest_rate, taxes_yr, insurance_yr, maint, mort, limit, ua_input, maint_capex, prop_mgmt_pct, loan_term_years, initial_repairs, proj, rent_growth, appreciation, closing_costs)
            st.download_button("📂 PDF Report", data=pdf.encode('latin-1'), file_name="Report.pdf", use_container_width=True)
            
    with e3: 
        st.download_button("📊 Export CSV", data=row.to_frame().T.to_csv().encode('utf-8'), file_name=f"Data_{selected_zip}.csv", use_container_width=True)

with tab_port:
    st.header("Portfolio")
    if not st.session_state.portfolio:
        st.info("No deals saved.")
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
        st.dataframe(pd.DataFrame(st.session_state.portfolio), use_container_width=True)

with tab_iq:
    st.header("IQ Center")
    st.markdown("### Resources")
    st.info("Section 8 Strategy Guide coming soon.")

render_footer()
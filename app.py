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

# --- 2. VISUAL UPGRADE: CUSTOM CSS (SaaS Look) ---
st.markdown("""
    <style>
    /* REMOVE DEFAULT PADDING */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
    }
    
    /* HIDE DEFAULT STREAMLIT ELEMENTS */
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* CUSTOM NAV BAR */
    .navbar {
        background-color: #1e3a8a; /* Deep Navy Blue */
        padding: 1rem 2rem;
        color: white;
        font-family: 'Helvetica', sans-serif;
        font-weight: 700;
        font-size: 24px;
        border-bottom: 4px solid #3b82f6; /* Lighter Blue Accent */
        margin-bottom: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* METRIC CARDS */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        color: #1e3a8a !important;
    }
    
    /* INPUT CONTAINERS (Cards) */
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
        
        available_cols = [c for c in rename_map.keys() if c in df.columns]
        df = df[available_cols].rename(columns=rename_map)
        
        # EXTRACT STATE
        df['state_abbr'] = df['area_name'].str.extract(r',\s([A-Z]{2})')
        df['state'] = df['state_abbr'].map(STATE_MAP)
        df['state'] = df['state'].fillna('Other')

        # Convert Rent to Numeric
        cols_to_numeric = ['Studio', '1-Bedroom', '2-Bedroom', '3-Bedroom', '4-Bedroom']
        for c in cols_to_numeric:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c].str.replace('$', '').str.replace(',', ''), errors='coerce').fillna(0)

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
        if len(data) > 1 and data[1][0]:
            rate = float(data[1][0])
            if rate >= 0:
                return rate 
    except:
        pass 

    try:
        url_raw = f"https://api.census.gov/data/2023/acs/acs5?get=B25004_002E,B25003_003E&for=zip%20code%20tabulation%20area:{zip_code}"
        r = requests.get(url_raw, timeout=3)
        data = r.json()
        if len(data) > 1:
            vacant_for_rent = float(data[1][0])
            renter_occupied = float(data[1][1])
            
            total_rental_inventory = vacant_for_rent + renter_occupied
            if total_rental_inventory > 0:
                calculated_rate = (vacant_for_rent / total_rental_inventory) * 100
                return round(calculated_rate, 1)
    except:
        pass 

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
    # Reverse calculates price based on target return
    test_price = 50000
    step = 1000
    for _ in range(1000): 
        loan = test_price * (1 - down_pct/100)
        monthly_pmt = calculate_mortgage(test_price, down_pct, interest_rate)
        cashflow_yr = (net_rent - (taxes/12) - (insurance/12) - maint_monthly - pm_monthly - monthly_pmt) * 12
        investment = (test_price * down_pct/100) + (test_price * closing_costs_pct/100) + repairs
        coc = (cashflow_yr / investment) * 100 if investment > 0 else 0
        
        if coc < target_coc:
            return test_price - step 
        test_price += step
    return 0

def calculate_projections(price, rent, total_expenses_yr, mortgage_yr, down_pct, interest_rate, term_years, growth_rate=0.02):
    # Generates 30-year wealth chart data
    data = []
    current_rent = rent * 12
    current_expenses = total_expenses_yr
    loan_balance = price * (1 - down_pct/100)
    
    for year in range(1, 31):
        # 1. Cash Flow
        noi = current_rent - current_expenses
        cashflow = noi - mortgage_yr
        
        # 2. Equity (Amortization)
        if loan_balance > 0:
            interest_payment = loan_balance * (interest_rate/100)
            principal_payment = mortgage_yr - interest_payment
            if principal_payment > loan_balance: principal_payment = loan_balance
            loan_balance -= principal_payment
        
        # 3. Appreciation
        property_value = price * ((1.02)**year)
        total_equity = property_value - loan_balance
        
        data.append({
            "Year": year,
            "Cash Flow": cashflow,
            "Loan Balance": loan_balance,
            "Total Equity": total_equity
        })
        
        # Inflate for next year
        current_rent *= (1 + growth_rate)
        current_expenses *= (1 + growth_rate)
        
    return pd.DataFrame(data)

# --- 6. MULTI-PAGE PDF GENERATOR ---
class ProPDF(FPDF):
    def header(self):
        # 1. SAFE WATERMARK (Centered, Light Gray)
        self.set_font('Helvetica', 'B', 50)
        self.set_text_color(240, 240, 240) 
        # Center horizontally (approx) and vertically
        self.set_xy(0, 110) 
        self.cell(210, 0, "YIELDMAP PRO", 0, 0, 'C')
        
        # 2. Professional Brand Banner (Draws OVER the watermark)
        self.set_fill_color(37, 99, 235)  # YieldMap Blue
        self.set_xy(0,0) # Reset to top
        self.rect(0, 0, 210, 22, 'F')
        
        # 3. Logo Integration
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 4, 35) 
        else:
            self.set_font('Helvetica', 'B', 20)
            self.set_text_color(255, 255, 255)
            self.set_xy(10, 6)
            self.cell(40, 10, "YieldMap", 0, 0, 'L')

        # 4. Report Title
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(0, 6)
        self.cell(210, 10, "SECTION 8 ANALYSIS REPORT", 0, 0, 'C')
        
        # 5. Date
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
        self.set_text_color(37, 99, 235) # Blue text
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y()) # Underline
        self.ln(2)

    def kpi_card(self, title, value, x, y, w=45, h=25):
        # Background Card
        self.set_xy(x, y)
        self.set_fill_color(248, 250, 252) # Very light gray
        self.set_draw_color(226, 232, 240) # Border color
        self.rect(x, y, w, h, 'DF')
        
        # Label
        self.set_xy(x, y+6)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(100, 116, 139) # Muted text
        self.cell(w, 5, title, 0, 1, 'C')
        
        # Value
        self.set_xy(x, y+13)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(37, 99, 235) # Brand Blue
        self.cell(w, 8, value, 0, 1, 'C')

    def add_table_row(self, label, value, fill=False):
        self.set_font('Helvetica', '', 10)
        self.set_fill_color(240, 253, 244) # Green tint
        self.cell(140, 8, label, 1, 0, 'L', fill)
        self.cell(50, 8, value, 1, 1, 'R', fill)

def generate_pro_report(client, address, row, unit, price, rent, v_rate, yield_val, coc_return, net_cashflow, d_grade, n_grade, down_pct, int_rate, taxes, ins, maint_cost, loan_pmt, hud_limit, ua_val, maint_pct, pm_pct, term_years, repairs, projections_df, rent_growth, appreciation):
    pdf = ProPDF()
    pdf.alias_nb_pages() # Enable total page count
    
    # --- PAGE 1: EXECUTIVE SUMMARY ---
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    area_name = row.get('area_name', 'Unknown')
    pdf.multi_cell(0, 8, f"Property Analysis: {area_name}")
    pdf.ln(2)
    
    # Client Info
    pdf.set_x(10)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(15, 6, "Client:", 0, 0, 'L')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(80, 6, client or "Valued Investor", 0, 0, 'L') 
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(15, 6, "Unit:", 0, 0, 'L')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(40, 6, unit, 0, 1, 'L')
    pdf.ln(6)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(17, 6, "Address:", 0, 0, 'L')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, address or "Not Specified", 0, 1, 'L')
    pdf.ln(8)

    # KPI Grid
    y_start = pdf.get_y()
    pdf.kpi_card("Deal Grade", f"{d_grade}", 10, y_start)
    pdf.kpi_card("Cash-on-Cash", f"{coc_return:.2f}%", 60, y_start)
    pdf.kpi_card("Monthly Flow", f"${net_cashflow:,.0f}", 110, y_start)
    pdf.kpi_card("Cap Rate", f"{yield_val:.2f}%", 160, y_start)
    pdf.ln(32)
    
    # Deal Grade Logic
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "*Deal Grade Logic: A+ (>12% CoC), B (8-12%), C (<8%). Based on conservative vacancy reserves.", 0, 1, 'L')
    pdf.ln(4)

    # Analysis Breakdown
    pdf.chapter_title("Financial Breakdown (Year 1)")
    pdf.add_table_row("Purchase Price", f"${price:,.0f}")
    pdf.add_table_row("HQS / Initial Repairs", f"${repairs:,.0f}")
    pdf.add_table_row("Total Cash Needed (Inc. Closing)", f"${(price*(down_pct/100)) + (price*0.03) + repairs:,.0f}", True)
    pdf.add_table_row("Loan Amount", f"${price*(1-down_pct/100):,.0f}")
    pdf.add_table_row("Monthly P&I Payment", f"${loan_pmt:,.2f}")
    pdf.ln(5)
    
    pdf.chapter_title("Section 8 Rent & Expenses")
    pdf.add_table_row("Gross HUD Rent", f"${rent:,.2f}")
    pdf.add_table_row("Vacancy Loss", f"(${rent * (v_rate/100):,.2f})")
    pdf.add_table_row("Effective Gross Income", f"${rent * (1 - v_rate/100):,.2f}", True)
    pdf.add_table_row("Property Taxes", f"(${taxes/12:,.2f})")
    pdf.add_table_row("Insurance", f"(${ins/12:,.2f})")
    pdf.add_table_row("Maintenance & CapEx", f"(${maint_cost:,.2f})")
    pdf.add_table_row("Property Management", f"(${rent * (pm_pct/100):,.2f})")
    pdf.add_table_row("Net Operating Income (NOI)", f"${(rent * (1 - v_rate/100)) - (taxes/12 + ins/12 + maint_cost + rent*(pm_pct/100)):,.2f}", True)

    # --- PAGE 2: WEALTH ACCUMULATION ---
    pdf.add_page()
    pdf.chapter_title("Buy & Hold Projections (Wealth Accumulation)")
    pdf.set_font('Helvetica', '', 9)
    # DYNAMIC TEXT
    pdf.multi_cell(0, 5, f"This projection assumes a conservative {rent_growth}% annual rent increase and {appreciation}% appreciation. It demonstrates the power of loan paydown (Amortization) in Section 8 investing.")
    pdf.ln(5)
    
    # Table Header
    pdf.set_fill_color(37, 99, 235) # Blue
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(20, 8, "Year", 1, 0, 'C', True)
    pdf.cell(40, 8, "Annual Cash Flow", 1, 0, 'C', True)
    pdf.cell(40, 8, "Loan Balance", 1, 0, 'C', True)
    pdf.cell(40, 8, "Total Equity", 1, 0, 'C', True)
    pdf.cell(40, 8, "Total Profit", 1, 1, 'C', True)
    
    # Table Rows
    pdf.set_text_color(50, 50, 50)
    pdf.set_font('Helvetica', '', 9)
    
    snapshot_years = [1, 2, 3, 5, 10, 20, 30]
    total_cf = 0
    initial_cash = (price*(down_pct/100)) + (price*0.03) + repairs
    
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

# --- 6. GAUGE COMPONENT ---
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

# --- 7. HELPER: WEB FOOTER ---
def render_footer():
    st.divider()
    st.markdown("""
    <div style="text-align: center; font-size: 12px; color: #64748b;">
        <p><strong>Yieldmappro.com</strong> | © 2025 All Rights Reserved</p>
        <p>Data Source: U.S. Housing & Urban Development (HUD) FY 2026 Small Area FMRs</p>
        <p style="font-style: italic;">Disclaimer: This tool is for educational purposes only and does not constitute financial advice. Always verify data with your local Housing Authority.</p>
    </div>
    """, unsafe_allow_html=True)

# --- 8. MAIN APP ---
df = load_data()
if df.empty: 
    st.error("DATABASE NOT FOUND: Please ensure 'hud_2026.xlsx' is uploaded.")
    st.stop()

# SESSION STATE INIT (Updated for Portfolio)
if 'agreed' not in st.session_state: st.session_state.agreed = False
if 'pro_unlocked' not in st.session_state: st.session_state.pro_unlocked = False
if 'portfolio' not in st.session_state: st.session_state.portfolio = [] # <--- NEW: Memory for deals

# --- TERMS OF SERVICE SCREEN ---
if not st.session_state.agreed:
    st.title("🔒 YieldMap Pro")
    
    with st.expander("📝 READ FULL TERMS OF USE & PRIVACY POLICY", expanded=True):
        st.markdown("""
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
        """)

    st.warning("⚠️ By checking the box below, you legally agree to these Terms.")
    
    # 1. THE CHECKBOX
    if st.checkbox("I have read and agree to the Terms of Use, Privacy Policy, and Limitation of Liability."):
        
        # 2. THE BUTTON
        if st.button("Accept & Enter Pro Analyzer"):
            st.session_state.agreed = True
            st.session_state.scroll_to_top = True
            st.rerun()

        # 3. AUTO-SCROLL DOWN (Aggressive Fix)
        st.markdown("""
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
            """, unsafe_allow_html=True)
            
    st.stop()

if st.session_state.get('scroll_to_top'):
    st.markdown("""
        <script>
            var body = window.parent.document.querySelector(".main");
            if (body) { body.scrollTop = 0; }
        </script>
        """, unsafe_allow_html=True)
    st.session_state.scroll_to_top = False

# --- HEADER SECTION (LOGO + SETTINGS) ---
c_head1, c_head2 = st.columns([5, 1])
with c_head1:
    st.markdown("""
        <div class="navbar">
            <span>YieldMap Pro</span>
            <span style="font-size: 14px; font-weight: 400; margin-left: auto; opacity: 0.8; font-family: monospace;">FY 2026 ENGINE</span>
        </div>
    """, unsafe_allow_html=True)

with c_head2:
    with st.popover("⚙️ Settings"):
        st.write("**Configuration**")
        st.caption("Enter API Keys or Configs here.")
        api_input = st.text_input("RentCast Key (Optional)", type="password")

# --- MAIN TABS (UPDATED FOR PHASE 3) ---
tab_anal, tab_port, tab_iq = st.tabs(["📊 Pro Analyzer", "📁 My Portfolio", "📖 IQ Center"])

# ==========================================
# TAB 1: PRO ANALYZER (EXISTING LOGIC)
# ==========================================
with tab_anal:
    # --- DRILL-DOWN SELECTORS (CARD STYLE) ---
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
            beds = st.selectbox("3. Unit Asset Class", ["Studio", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom"], index=2, help="Select bedroom count.")

    row = df[df['zip_code'] == selected_zip].iloc[0]
    market_area_name = row.get('area_name', 'Unknown Area')

    # --- COMPETITOR-GRADE 2D MAP (FOLIUM) ---
    st.markdown("---")
    st.markdown(f"#### 📍 {market_area_name} ({selected_zip})")
    try:
        import pgeocode
        import folium
        from streamlit_folium import st_folium
        
        nomi = pgeocode.Nominatim('us')
        loc = nomi.query_postal_code(selected_zip)
        
        if not math.isnan(loc.latitude) and not math.isnan(loc.longitude):
            # Create the Map (Centered on ZIP)
            m = folium.Map(
                location=[loc.latitude, loc.longitude], 
                zoom_start=13,
                tiles="OpenStreetMap" 
            )
            
            # Add a Professional Marker
            folium.Marker(
                [loc.latitude, loc.longitude], 
                popup=f"Target ZIP: {selected_zip}",
                tooltip="Analysis Center",
                icon=folium.Icon(color="blue", icon="home", prefix='fa')
            ).add_to(m)
            
            # Render map
            st_folium(m, width=None, height=400, use_container_width=True)
            
        else:
            st.warning(f"Could not map coordinates for ZIP {selected_zip}")
            
    except ImportError:
        st.error("🚨 Map Libraries Missing. Run 'pip install streamlit-folium folium pgeocode'")
    except Exception as e:
        st.caption(f"Map unavailable: {e}")

    # UNDERWRITING (CARD STYLE)
    st.markdown("---")
    limit = row[beds]
    
    with st.container(border=True):
        st.markdown(f"#### ⚡ Pro Underwriting: {market_area_name} (ZIP {selected_zip})")
        col_u_inputs, col_u_info = st.columns([2, 1])
        with col_u_inputs:
            col_p1, col_p2, col_p3 = st.columns(3)
            if 'ua_value' not in st.session_state: st.session_state.ua_value = 150
            if col_p1.button("Low ($120)"): st.session_state.ua_value = 120
            if col_p2.button("Mid ($180)"): st.session_state.ua_value = 180
            if col_p3.button("High ($250)"): st.session_state.ua_value = 250
            
            ua_input = st.slider("Utility Allowance Deduction", 0, 400, value=st.session_state.ua_value, help="The amount you must deduct from the rent if the tenant pays their own utilities.")
            st.caption("⚠️ **Verification Required:** Consult local PHA.")
        
        target_rent = limit - ua_input
        with col_u_info:
            st.info(f"**HUD FY 2026 Limit:** ${limit:,.0f} \n\n**Net Contract Rent:** ${target_rent:,.0f}")
    
    with st.container(border=True):
        st.markdown("#### Acquisition Details")
        col_in1, col_in2 = st.columns(2)
        with col_in1: 
            price = st.number_input("Acquisition Price ($)", value=250000, help="The total purchase price of the property.")
        with col_in2: 
            rent_in = st.number_input("Target Contract Rent ($)", value=int(target_rent), help="The actual rent you expect to collect.")
        
        # --- ADVANCED CONFIGURATION ---
        api_vacancy = get_vacancy_rate(selected_zip)
        is_unlocked = st.session_state.pro_unlocked
        start_val = api_vacancy if api_vacancy is not None else 5.0
        
        with st.expander("⚙️ Advanced Configuration (Pro Features)", expanded=True):
            if not is_unlocked:
                st.caption("🔒 **These inputs are locked. Upgrade to Pro to customize assumptions.**")
                
            c1, c2 = st.columns(2)
            with c1:
                user_vacancy = st.number_input("Vacancy Rate (%)", value=start_val, step=0.1, disabled=not is_unlocked, help="Adjust estimated vacancy rate (Pro Only).")
                down_payment = st.number_input("Down Payment (%)", value=20.0, step=5.0, disabled=not is_unlocked, help="Pro Only")
                interest_rate = st.number_input("Interest Rate (%)", value=7.0, step=0.1, disabled=not is_unlocked, help="Pro Only")
                loan_term_years = st.number_input("Loan Term (Years)", value=30, step=5, disabled=not is_unlocked, help="Standard is 30 years.")
                # NEW: Section 8 Repairs
                initial_repairs = st.number_input("HQS Repair Budget ($)", value=2000, step=500, disabled=not is_unlocked, help="Upfront fixes to pass Section 8 inspection.")
                # NEW: APPRECIATION & RENT GROWTH INPUTS
                appreciation = st.number_input("Appreciation %", value=2.0, step=0.5, disabled=not is_unlocked, help="Annual property value increase.")
                rent_growth = st.number_input("Rent Growth %", value=2.0, step=0.5, disabled=not is_unlocked, help="Annual rent increase.")
            with c2:
                taxes_yr = st.number_input("Property Taxes ($/yr)", value=3000, disabled=not is_unlocked, help="Pro Only")
                insurance_yr = st.number_input("Insurance ($/yr)", value=1200, disabled=not is_unlocked, help="Pro Only")
                maint_capex = st.slider("Maint/CapEx (%)", 0, 20, 10, disabled=not is_unlocked, help="Pro Only")
                prop_mgmt_pct = st.number_input("Property Mgmt (%)", value=8.0, step=1.0, disabled=not is_unlocked, help="Standard fee is 8-10%. Set to 0 if self-managed.")
                closing_costs = st.number_input("Closing Costs (%)", value=3.0, step=0.5, disabled=not is_unlocked, help="Est. 3-5% of purchase price. Set to 0 if seller pays.")
                # NEW: Target CoC
                target_coc_input = st.number_input("Target CoC Return (%)", value=12.0, step=1.0, disabled=not is_unlocked, help="Used to calculate Max Allowable Offer.")

    # --- CALCULATIONS ---
    gross_annual_rent = rent_in * 12
    vacancy_loss_annual = gross_annual_rent * (user_vacancy / 100)
    effective_gross_income = gross_annual_rent - vacancy_loss_annual
    maint_amount = effective_gross_income * (maint_capex / 100)
    prop_mgmt_amount = gross_annual_rent * (prop_mgmt_pct / 100)
    
    total_expenses = taxes_yr + insurance_yr + maint_amount + prop_mgmt_amount
    noi = effective_gross_income - total_expenses
    
    monthly_mortgage = calculate_mortgage(price, down_payment, interest_rate, loan_term_years)
    annual_debt_service = monthly_mortgage * 12
    
    annual_cash_flow = noi - annual_debt_service
    monthly_cash_flow = annual_cash_flow / 12
    # UPDATED: Investment includes repairs
    initial_investment = (price * (down_payment / 100)) + (price * (closing_costs / 100)) + initial_repairs
    coc_return = (annual_cash_flow / initial_investment) * 100 if initial_investment > 0 else 0
    yield_val = (rent_in * 12 / price * 100) if price > 0 else 0

    # GRADING
    if limit >= 2500: n_grade = "A"
    elif limit >= 1800: n_grade = "B"
    elif limit >= 1200: n_grade = "C"
    else: n_grade = "D"

    if coc_return >= 12: d_grade = "A+"
    elif coc_return >= 8: d_grade = "B"
    else: d_grade = "C"

    # --- TEASER DASHBOARD ---
    st.divider()
    logo_base64 = ""
    if os.path.exists("logo.png"):
        logo_base64 = base64.b64encode(open("logo.png", "rb").read()).decode()
        st.markdown(f'<div class="rating-title"><img src="data:image/png;base64,{logo_base64}" width="60"><h2 class="rating-text">YieldMap Asset Rating</h2></div>', unsafe_allow_html=True)
    else:
        st.markdown("## YieldMap Asset Rating")

    # SAFETY CHECK FOR PRO VAR
    if 'pro_unlocked' not in st.session_state:
        st.session_state.pro_unlocked = False
    
    is_pro = st.session_state.pro_unlocked
    
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Deal Grade", f"Grade {d_grade}" if is_pro else "🔒 Pro", help="Based on Cash-on-Cash Return.")
    r2.metric("Cash-on-Cash", f"{coc_return:.1f}%" if is_pro else "🔒 Pro", help="Net Profit / Cash Invested.")
    r3.metric("Net Monthly Flow", f"${monthly_cash_flow:,.0f}" if is_pro else "🔒 Pro", help="Profit after mortgage & expenses.")
    r4.metric("Total Cash Needed", f"${initial_investment:,.0f}" if is_pro else "🔒 Pro", help="Includes Down Pmt + Closing + HQS Repairs")

    # --- NEW: MAX OFFER CALCULATOR ---
    if is_pro:
        mao_price = calculate_max_offer(rent_in * (1-user_vacancy/100), target_coc_input, initial_repairs, closing_costs, down_payment, interest_rate, taxes_yr, insurance_yr, maint_amount/12, prop_mgmt_amount/12)
        st.info(f"🎯 **Max Allowable Offer (MAO):** To hit a **{target_coc_input}% CoC**, you should pay no more than **${mao_price:,.0f}** for this property.")
    else:
        st.info("🎯 **Max Allowable Offer (MAO):** 🔒 Unlock Pro to see the exact price you should pay to hit your target return.")

    st.divider()
    g1, g2 = st.columns(2)
    with g1: 
        if is_pro:
            st.markdown('<p class="chart-label">Cash on Cash Return</p>', unsafe_allow_html=True)
            # FIX APPLIED: Hide Toolbar
            st.plotly_chart(create_gauge(coc_return, "CoC %", 0, 20), use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("🔒 Cash-on-Cash Gauge Locked")
    with g2: 
        if is_pro:
            # NEW: Equity Chart instead of Vacancy Gauge
            st.markdown('<p class="chart-label">5-Year Equity Projection</p>', unsafe_allow_html=True)
            years = list(range(1, 6))
            equity_vals = []
            current_bal = price * (1 - down_payment/100)
            for y in years:
                # Simple amortization approximation
                paid_principal = (monthly_mortgage * 12) - (current_bal * interest_rate/100)
                if paid_principal < 0: paid_principal = 0 # Interest only guard
                current_bal -= paid_principal
                equity = price * ((1 + appreciation/100)**y) - current_bal
                equity_vals.append(equity)
            
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(x=years, y=equity_vals, fill='tozeroy', mode='none', fillcolor='rgba(37, 99, 235, 0.5)'))
            fig_eq.update_layout(height=180, margin=dict(l=20, r=20, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(showgrid=False, fixedrange=True), yaxis=dict(showgrid=False, fixedrange=True))
            st.plotly_chart(fig_eq, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
        else:
            st.info("🔒 Equity Chart Locked")

    # --- PRO GATE (SAFE MODE) ---
    st.divider()
    
    # SAFE SECRET RETRIEVAL
    try:
        PRO_CODE = st.secrets["PRO_CODE"]
    except:
        PRO_CODE = "1234" # Fallback if secrets.toml is missing locally
        
    e1, e2, e3 = st.columns(3) # <--- UPDATED: 3 COLUMNS FOR SAVE / PDF / CSV
    
    with e1:
        if is_pro:
            # SAVE BUTTON (Phase 3 Fix)
            if st.button("💾 Save Deal", type="primary", use_container_width=True):
                deal_data = {
                    "Address": prop_address or f"ZIP {selected_zip}",
                    "Price": price,
                    "Rent": rent_in,
                    "CoC": coc_return,
                    "Cashflow": monthly_cash_flow,
                    "Grade": d_grade,
                    "Repairs": initial_repairs,
                    "Timestamp": datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.portfolio.append(deal_data)
                st.success("Saved!")
        else:
            st.warning("🔓 **Unlock Pro Features**")
            c_input = st.text_input("Enter Access Code", type="password", placeholder="Enter code to unlock")
            if c_input == PRO_CODE:
                st.session_state.pro_unlocked = True
                st.success("Access Granted!")
                st.rerun()
            elif c_input:
                st.error("Invalid Code")

    with e2:
        if is_pro:
            # PDF BUTTON
            # GENERATE PROJECTIONS FOR PDF
            proj_df = calculate_projections(price, rent_in, total_expenses, annual_debt_service, down_payment, interest_rate, loan_term_years, rent_growth, appreciation)
            pdf_bytes = generate_pro_report(client_name, prop_address, row, beds, price, rent_in, user_vacancy, yield_val, coc_return, monthly_cash_flow, d_grade, n_grade, down_payment, interest_rate, taxes_yr, insurance_yr, maint_amount/12, monthly_mortgage, limit, ua_input, maint_capex, prop_mgmt_pct, loan_term_years, initial_repairs, proj_df, rent_growth, appreciation)
            st.download_button("📂 Download PDF", data=pdf_bytes.encode('latin-1'), file_name=f"Report_{selected_zip}.pdf", use_container_width=True)

    with e3: 
        # CSV BUTTON
        st.download_button("📊 Export CSV", data=row.to_frame().T.to_csv().encode('utf-8'), file_name=f"Data_{selected_zip}.csv", use_container_width=True)
    
    render_footer()

# ==========================================
# TAB 2: PORTFOLIO (NEW LOCATION)
# ==========================================
with tab_port:
    st.header("⚖️ Portfolio Command Center")
    
    if len(st.session_state.portfolio) == 0:
        st.info("Your portfolio is empty. Go to the **Pro Analyzer** tab, run a deal, and click **'Save Deal'**.")
    else:
        # 1. MANAGE DEALS SECTION
        st.markdown("### 📋 Manage Deals")
        for i, deal in enumerate(st.session_state.portfolio):
            with st.expander(f"🏠 {deal['Address']} (Grade: {deal['Grade']})"):
                c1, c2, c3 = st.columns([2,2,1])
                c1.write(f"**Price:** ${deal['Price']:,.0f}")
                c2.write(f"**CoC:** {deal['CoC']:.1f}%")
                if c3.button("🗑️ Delete", key=f"port_del_{i}"):
                    st.session_state.portfolio.pop(i)
                    st.rerun()
        
        st.divider()
        
        # 2. COMPARISON MATRIX
        st.markdown("### 📊 Comparison Matrix")
        comp_df = pd.DataFrame(st.session_state.portfolio)
        
        # Highlight logic (Pandas Styler)
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
        
        # 3. CHARTS
        st.markdown("### 📈 Performance Visualizer")
        c1, c2 = st.columns(2)
        with c1:
            fig_coc = go.Figure(data=[go.Bar(x=comp_df['Address'], y=comp_df['CoC'], marker_color='#2563eb')])
            fig_coc.update_layout(title="Cash-on-Cash Return (%)", yaxis_title="CoC %", staticPlot=True)
            st.plotly_chart(fig_coc, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
        with c2:
            fig_cf = go.Figure(data=[go.Bar(x=comp_df['Address'], y=comp_df['Cashflow'], marker_color='#10b981')])
            fig_cf.update_layout(title="Monthly Cashflow ($)", yaxis_title="Cashflow $", staticPlot=True)
            st.plotly_chart(fig_cf, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

# ==========================================
# TAB 3: IQ CENTER (EXISTING CONTENT)
# ==========================================
with tab_iq:
    st.header("YieldMap IQ Center: Expert Knowledge Base")
    st.markdown("---")
    
    st.subheader("1. Pro Metrics Explained")
    st.markdown("""
    * **Cash-on-Cash Return (CoC):** The most important metric for investors. It measures the annual net cash flow divided by your total cash investment (Down payment + Closing costs). A CoC of 12% is generally considered excellent.
    * **Net Monthly Cashflow:** The actual money left in your bank account each month after paying the Mortgage, Taxes, Insurance, Maintenance (Reserves), and Vacancy losses.
    * **Operating Expense Ratio (OER):** The percentage of your gross income that goes to operating expenses (excluding mortgage).
    """)
    st.markdown("---")

    st.subheader("2. Strategic Investment Grading")
    col_iq1, col_iq2 = st.columns(2)
    
    with col_iq1:
        st.markdown("#### Neighborhood Grades (Risk Profile)")
        st.caption("Based on FY 2026 Rent Ceilings (Income Proxy).")
        st.markdown("""
        * **Grade A (Prime / >$2500 Rent):** High appreciation, lower yield. Best for long-term hold.
        * **Grade B (Strong / $1800-$2500):** Balanced performance.
        * **Grade C (Stable / $1200-$1800):** The "Sweet Spot" for Section 8. High demand, solid yield.
        * **Grade D (Working / <$1200):** High cash flow potential but requires intensive management.
        """)
        
    with col_iq2:
        st.markdown("#### Deal Grades (Performance Index)")
        st.caption("Calculated using Cash-on-Cash Return.")
        st.markdown("""
        * **Grade A+ (Unicorn):** CoC > 12%. Immediate Buy.
        * **Grade B (Core Asset):** CoC 8-12%. Solid portfolio builder.
        * **Grade C (Average):** CoC < 8%. Average market return.
        * **Grade D (Distressed):** Negative cash flow or high risk.
        """)

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
        st.markdown("""
        * **Low ($120):** Modern Apartments, Gas Heat, Landlord pays Water/Sewer.
        * **Mid ($180):** Row Homes/Townhomes. Tenant pays Electric & Gas.
        * **High ($250):** Older Detached Homes, Oil/Electric Heat, Poor Insulation.
        """)
        st.caption("*Always download the specific UA Schedule from the local Housing Authority.*")

    st.markdown("---")
    
    st.subheader("4. Inspections & The 'Auto-Fail' List")
    st.write("Before you get paid, you must pass the HQS (Housing Quality Standards) Inspection. Here are the top failure items:")
    
    with st.expander("🚨 The Top 5 Inspection Failures (Check these first!)", expanded=True):
        st.markdown("""
        1.  **Peeling Paint:** If the home was built before 1978, *any* chipping or peeling paint (interior or exterior) is an automatic fail due to lead risk.
        2.  **Window Locks:** Every single window that is accessible from the outside (1st floor) must have a working lock.
        3.  **Water Heater TPR Valve:** The discharge pipe on the water heater must be copper/metal and end within 6 inches of the floor.
        4.  **Smoke & Carbon Detectors:** Must be present on every floor and in every bedroom.
        5.  **Trip Hazards:** Torn carpet, uneven concrete, or loose floorboards will fail.
        """)
        
    st.markdown("#### The 'Golden' Lease-Up Timeline")
    st.info("1. **Find Tenant** -> 2. **Submit RFTA (Request for Tenancy Approval)** -> 3. **Rent Determination** -> 4. **Inspection** -> 5. **Lease Sign** -> 6. **First Payment (can take 30-60 days)**")

    st.markdown("---")

    col_iq5, col_iq6 = st.columns(2)
    with col_iq5:
        st.subheader("5. The YieldMap Score")
        st.write("Our 100-point risk index is weighted as follows:")
        st.progress(40); st.caption("40% - HUD Rent Safety (Is the rent legal?)")
        st.progress(30); st.caption("30% - Gross Yield (Is the return high?)")
        st.progress(30); st.caption("30% - Absorption (Can we find a tenant?)")

    with col_iq6:
        st.subheader("6. Glossary of Terms")
        st.markdown("""
        * **FMR (Fair Market Rent):** HUD's gross rent limit for a county/zip.
        * **VPS (Voucher Payment Standard):** The actual amount the local PHA decides to pay (usually 90-110% of FMR).
        * **HAP Contract:** The contract between you and the PHA (Housing Authority).
        * **RFTA:** Request for Tenancy Approval (The 'packet' the tenant gives you).
        """)

    render_footer()

# --- OPTIONAL: TESTER CODE ---
if __name__ == "__main__":

    pass
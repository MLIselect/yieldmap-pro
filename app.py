import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import os
import base64
from datetime import datetime
import requests
import math 

# --- 1. PRO CONFIGURATION ---
st.set_page_config(
    page_title="YieldMap Pro | Deal Analyzer",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- HIDE STREAMLIT BRANDING ---
hide_st_style = """
    <style>
    footer {visibility: hidden;}
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    button[title="View fullscreen"] {visibility: hidden; display: none;}
    .stApp > header {display: none;}
    [data-testid="stDecoration"] {display:none;}
    [data-testid="stToolbar"] {display:none;}
    </style>
    """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. REFERENCE DATA (STATE NAMES) ---
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

# --- 3. DATA UTILITIES (FY 2026 ENGINE) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("hud_2026.xlsx", header=0, dtype=str)
        df.columns = df.columns.astype(str).str.replace('\n', '_').str.replace(' ', '_').str.upper().str.strip()
        if 'ZIP_CODE' in df.columns:
            df = df.dropna(subset=['ZIP_CODE'])
        
        rename_map = {
            'ZIP_CODE': 'zip_code', 'ZIP': 'zip_code',
            'SAFMR_0BR': 'Studio', 'SAFMR_1BR': '1-Bedroom', 
            'SAFMR_2BR': '2-Bedroom', 'SAFMR_3BR': '3-Bedroom',
            'SAFMR_4BR': '4-Bedroom', 'HUD_FAIR_MARKET_RENT_AREA_NAME': 'area_name'
        }
        
        available_cols = [c for c in rename_map.keys() if c in df.columns]
        df = df[available_cols].rename(columns=rename_map)
        df['state_abbr'] = df['area_name'].str.extract(r',\s([A-Z]{2})')
        df['state'] = df['state_abbr'].map(STATE_MAP).fillna('Other')

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
            return float(data[1][0])
    except:
        pass
    try:
        url_raw = f"https://api.census.gov/data/2023/acs/acs5?get=B25004_002E,B25003_003E&for=zip%20code%20tabulation%20area:{zip_code}"
        r = requests.get(url_raw, timeout=3)
        data = r.json()
        if len(data) > 1:
            vacant = float(data[1][0])
            occupied = float(data[1][1])
            if (vacant + occupied) > 0:
                return round((vacant / (vacant + occupied)) * 100, 1)
    except:
        pass
    return 5.0

# --- 4. FINANCIAL MATH ENGINE ---
def calculate_mortgage(price, down_payment_pct, interest_rate, term_years=30):
    loan_amount = price * (1 - (down_payment_pct/100))
    if loan_amount <= 0: return 0
    monthly_rate = (interest_rate / 100) / 12
    num_payments = term_years * 12
    if monthly_rate == 0: return loan_amount / num_payments
    return loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)

# --- 5. PDF GENERATOR ---
class ProPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 50)
        self.set_text_color(240, 240, 240)
        self.set_xy(0, 110) 
        self.cell(210, 0, "YIELDMAP PRO", 0, 0, 'C')
        self.set_fill_color(37, 99, 235)
        self.set_xy(0,0)
        self.rect(0, 0, 210, 22, 'F')
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 4, 35) 
        else:
            self.set_font('Helvetica', 'B', 20)
            self.set_text_color(255, 255, 255)
            self.set_xy(10, 6)
            self.cell(40, 10, "YieldMap", 0, 0, 'L')
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(0, 6)
        self.cell(210, 10, "INVESTMENT ANALYSIS REPORT", 0, 0, 'C')
        self.set_font('Helvetica', '', 9)
        self.set_xy(160, 6)
        self.cell(40, 10, datetime.now().strftime('%Y-%m-%d'), 0, 0, 'R')
        self.ln(18)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'YieldMap Pro | Powered by HUD.gov & US Census | Page {self.page_no()} of {{nb}}', 0, 0, 'C')

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
        self.set_xy(x, y+6)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(100, 116, 139)
        self.cell(w, 5, title, 0, 1, 'C')
        self.set_xy(x, y+13)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(37, 99, 235)
        self.cell(w, 8, value, 0, 1, 'C')

def generate_pro_report(client, address, row, unit, price, rent, v_rate, yield_val, coc_return, net_cashflow, d_grade, n_grade, down_pct, int_rate, taxes, ins, maint_cost, loan_pmt, hud_limit, ua_val, maint_pct, pm_pct, term_years):
    pdf = ProPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    area_name = row.get('area_name', 'Unknown')
    pdf.multi_cell(0, 8, f"Property Analysis: {area_name}")
    pdf.ln(2)
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
    y_start = pdf.get_y()
    pdf.kpi_card("Deal Grade", f"{d_grade}", 10, y_start)
    pdf.kpi_card("Cash-on-Cash", f"{coc_return:.2f}%", 60, y_start)
    pdf.kpi_card("Monthly Flow", f"${net_cashflow:,.0f}", 110, y_start)
    pdf.kpi_card("Cap Rate", f"{yield_val:.2f}%", 160, y_start)
    pdf.ln(32)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "*Deal Grade Logic: A+ (>12% CoC), B (8-12%), C (<8%). Based on conservative vacancy reserves.", 0, 1, 'L')
    pdf.ln(4)
    pdf.chapter_title("Acquisition & Assumptions")
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    col_w = 47; h = 8
    pdf.cell(col_w, h, "Purchase Price", 1); pdf.cell(col_w, h, f"${price:,.0f}", 1)
    pdf.cell(col_w, h, "Down Payment", 1); pdf.cell(col_w, h, f"{down_pct:.1f}% (${price*(down_pct/100):,.0f})", 1)
    pdf.ln()
    pdf.cell(col_w, h, "Loan Amount", 1); pdf.cell(col_w, h, f"${price*(1-down_pct/100):,.0f}", 1)
    pdf.cell(col_w, h, "Interest Rate", 1); pdf.cell(col_w, h, f"{int_rate:.2f}% ({term_years}yr)", 1)
    pdf.ln()
    pdf.cell(col_w, h, "HUD FY26 Limit", 1); pdf.cell(col_w, h, f"${hud_limit:,.0f}", 1)
    pdf.cell(col_w, h, "Utility Allowance", 1); pdf.cell(col_w, h, f"${ua_val:,.0f}", 1)
    pdf.ln()
    pdf.cell(col_w, h, "Total Investment", 1); pdf.cell(col_w, h, f"${(price*(down_pct/100)) + (price*0.03):,.0f}", 1) 
    pdf.cell(col_w, h, "Est. Closing Costs", 1); pdf.cell(col_w, h, "3.0%", 1)
    pdf.ln(10)
    pdf.chapter_title("Pro Forma Monthly Cash Flow")
    pdf.set_fill_color(226, 232, 240)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(140, 8, "Item", 1, 0, 'L', True)
    pdf.cell(50, 8, "Amount", 1, 1, 'R', True)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(140, 8, "Net Contract Rent (Gross Income)", 1)
    pdf.cell(50, 8, f"${rent:,.2f}", 1, 1, 'R')
    pdf.cell(140, 8, f"Less: Vacancy Loss ({v_rate:.1f}%)", 1)
    pdf.set_text_color(220, 38, 38)
    pdf.cell(50, 8, f"(${rent * (v_rate/100):,.2f})", 1, 1, 'R')
    pdf.set_text_color(50, 50, 50)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(240, 253, 244)
    pdf.cell(140, 8, "Effective Gross Income", 1, 0, 'L', True)
    pdf.cell(50, 8, f"${rent * (1 - v_rate/100):,.2f}", 1, 1, 'R', True)
    pdf.set_font('Helvetica', '', 10)
    expenses = [
        ("Property Taxes", taxes/12),
        ("Insurance", ins/12),
        (f"Maintenance & CapEx ({maint_pct}%)", maint_cost),
        (f"Property Management ({pm_pct}%)", rent * (pm_pct/100)),
        ("Debt Service (Principal & Interest)", loan_pmt)
    ]
    total_exp = 0
    for label, amount in expenses:
        pdf.cell(140, 8, label, 1)
        pdf.cell(50, 8, f"(${amount:,.2f})", 1, 1, 'R')
        total_exp += amount
    pdf.ln(2)
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 12)
    final_cashflow = (rent * (1 - v_rate/100)) - total_exp
    pdf.cell(140, 12, "NET MONTHLY CASH FLOW", 1, 0, 'L', True)
    pdf.cell(50, 12, f"${final_cashflow:,.2f}", 1, 1, 'R', True)
    pdf.set_text_color(50, 50, 50)
    pdf.ln(15)
    if pdf.get_y() > 240: 
        pdf.add_page()
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(0, 5, "LEGAL DISCLAIMER & LIMITATION OF LIABILITY", 0, 1, 'L')
    pdf.set_font('Helvetica', '', 7)
    pdf.multi_cell(0, 4, "Disclaimer: Educational Use Only. Verify all data with local PHA.")
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
    st.markdown("""<div style="text-align: center; color: #64748b;">Yieldmappro.com | © 2025</div>""", unsafe_allow_html=True)

# --- 8. MAIN APP ---
df = load_data()
if df.empty: 
    st.error("DATABASE NOT FOUND: Please ensure 'hud_2026.xlsx' is uploaded.")
    st.stop()

if 'agreed' not in st.session_state: st.session_state.agreed = False
if 'pro_unlocked' not in st.session_state: st.session_state.pro_unlocked = False

# --- TERMS OF SERVICE SCREEN ---
if not st.session_state.agreed:
    st.title("🔒 YieldMap Pro")
    with st.expander("📝 READ FULL TERMS OF USE", expanded=True):
        st.markdown("""
        ### **TERMS OF USE**
        **Effective Date:** December 30, 2025
        1. **No Financial Advice:** This is an educational tool.
        2. **Data Verification:** You must verify FMRs with the local PHA.
        3. **Liability:** We are not liable for investment losses.
        4. **Governing Law:** United States.
        """)

    st.warning("⚠️ By checking the box below, you legally agree to these Terms.")
    
    # 1. THE CHECKBOX
    if st.checkbox("I have read and agree to the Terms of Use."):
        
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
                        container.scrollTo({top: container.scrollHeight, behavior: 'smooth'});
                    }
                }, 300);
            </script>
            """, unsafe_allow_html=True)
            
    st.stop()

# --- SCROLL TO TOP FIX (Runs after the page reloads) ---
if st.session_state.get('scroll_to_top'):
    st.markdown("""
        <script>
            var body = window.parent.document.querySelector(".main");
            if (body) { body.scrollTop = 0; }
        </script>
        """, unsafe_allow_html=True)
    st.session_state.scroll_to_top = False

# STYLING
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .hero { background: linear-gradient(135deg, #2563eb, #10b981); padding: 2.5rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

tab_anal, tab_iq = st.tabs(["📊 Pro Analyzer", "📖 IQ Center"])

with tab_anal:
    if os.path.exists("logo.png"):
        st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="data:image/png;base64,{base64.b64encode(open("logo.png", "rb").read()).decode()}" width="400"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero"><h1>YieldMap Pro</h1><p>Market Intelligence • FY 2026</p></div>', unsafe_allow_html=True)

    # NEW: Property Address Input
    c_client, c_addr = st.columns(2)
    with c_client:
        client_name = st.text_input("Prepared For", placeholder="e.g. Acme Properties LLC")
    with c_addr:
        prop_address = st.text_input("Property Address", placeholder="e.g. 123 Main St, Rome, GA")
    
    col_input1, col_input2, col_input3 = st.columns(3)
    with col_input1:
        state_list = sorted([s for s in df['state'].unique() if s != 'Other'])
        selected_state = st.selectbox("1. Select State", state_list)
    with col_input2:
        zip_list = sorted(df[df['state'] == selected_state]['zip_code'].unique())
        selected_zip = st.selectbox("2. Select ZIP Code", zip_list)
    with col_input3:
        beds = st.selectbox("3. Unit Asset Class", ["Studio", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom"], index=2)

    row = df[df['zip_code'] == selected_zip].iloc[0]
    limit = row[beds]
    
    col_u_inputs, col_u_info = st.columns([2, 1])
    with col_u_inputs:
        if 'ua_value' not in st.session_state: st.session_state.ua_value = 150
        ua_input = st.slider("Utility Allowance Deduction", 0, 400, value=st.session_state.ua_value)
    
    target_rent = limit - ua_input
    with col_u_info:
        st.info(f"**HUD FY 2026 Limit:** ${limit:,.0f} \n\n**Net Contract Rent:** ${target_rent:,.0f}")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1: price = st.number_input("Acquisition Price ($)", value=250000)
    with col_in2: rent_in = st.number_input("Target Contract Rent ($)", value=int(target_rent))
    
    # --- ADVANCED CONFIGURATION ---
    api_vacancy = get_vacancy_rate(selected_zip)
    is_unlocked = st.session_state.pro_unlocked
    start_val = api_vacancy if api_vacancy is not None else 5.0
    
    with st.expander("⚙️ Advanced Configuration (Pro Features)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            user_vacancy = st.number_input("Vacancy Rate (%)", value=start_val, step=0.1, disabled=not is_unlocked)
            down_payment = st.number_input("Down Payment (%)", value=20.0, step=5.0, disabled=not is_unlocked)
            interest_rate = st.number_input("Interest Rate (%)", value=7.0, step=0.1, disabled=not is_unlocked)
            loan_term_years = st.number_input("Loan Term (Years)", value=30, step=5, disabled=not is_unlocked)
        with c2:
            taxes_yr = st.number_input("Property Taxes ($/yr)", value=3000, disabled=not is_unlocked)
            insurance_yr = st.number_input("Insurance ($/yr)", value=1200, disabled=not is_unlocked)
            maint_capex = st.slider("Maint/CapEx (%)", 0, 20, 10, disabled=not is_unlocked)
            prop_mgmt_pct = st.number_input("Property Mgmt (%)", value=8.0, step=1.0, disabled=not is_unlocked)
            closing_costs = st.number_input("Closing Costs (%)", value=3.0, step=0.5, disabled=not is_unlocked)

    # --- CALCULATIONS ---
    gross_annual_rent = rent_in * 12
    vacancy_loss_annual = gross_annual_rent * (user_vacancy / 100)
    effective_gross_income = gross_annual_rent - vacancy_loss_annual
    maint_amount = effective_gross_income * (maint_capex / 100)
    prop_mgmt_amount = gross_annual_rent * (prop_mgmt_pct / 100)
    total_expenses = taxes_yr + insurance_yr + maint_amount + prop_mgmt_amount
    noi = effective_gross_income - total_expenses
    monthly_mortgage = calculate_mortgage(price, down_payment, interest_rate, loan_term_years)
    annual_cash_flow = noi - (monthly_mortgage * 12)
    monthly_cash_flow = annual_cash_flow / 12
    initial_investment = (price * (down_payment / 100)) + (price * (closing_costs / 100))
    coc_return = (annual_cash_flow / initial_investment) * 100 if initial_investment > 0 else 0
    yield_val = (rent_in * 12 / price * 100) if price > 0 else 0

    if limit >= 2500: n_grade = "A"
    elif limit >= 1800: n_grade = "B"
    elif limit >= 1200: n_grade = "C"
    else: n_grade = "D"
    if coc_return >= 12: d_grade = "A+"
    elif coc_return >= 8: d_grade = "B"
    else: d_grade = "C"

    # --- DASHBOARD ---
    st.divider()
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Deal Grade", f"Grade {d_grade}" if is_pro else "🔒 Pro")
    r2.metric("Cash-on-Cash", f"{coc_return:.1f}%" if is_pro else "🔒 Pro")
    r3.metric("Net Monthly Flow", f"${monthly_cash_flow:,.0f}" if is_pro else "🔒 Pro")
    r4.metric("Vacancy Rate", f"{user_vacancy:.1f}%" if is_pro else "🔒 Pro")

    st.divider()
    g1, g2 = st.columns(2)
    with g1: 
        if is_pro: st.plotly_chart(create_gauge(coc_return, "CoC %", 0, 20), use_container_width=True)
        else: st.info("🔒 Cash-on-Cash Gauge Locked")
    with g2: 
        if is_pro: st.plotly_chart(create_gauge(user_vacancy, "Vacancy", 0, 15, flip=True), use_container_width=True)
        else: st.info("🔒 Vacancy Gauge Locked")

    # --- PRO GATE ---
    st.divider()
    PRO_CODE = st.secrets["PRO_CODE"]
    e1, e2 = st.columns(2)
    with e1:
        if is_pro:
            pdf_bytes = generate_pro_report(client_name, prop_address, row, beds, price, rent_in, user_vacancy, yield_val, coc_return, monthly_cash_flow, d_grade, n_grade, down_payment, interest_rate, taxes_yr, insurance_yr, maint_amount/12, monthly_mortgage, limit, ua_input, maint_capex, prop_mgmt_pct, loan_term_years)
            st.download_button("📂 Download PDF", data=pdf_bytes.encode('latin-1'), file_name=f"Report_{selected_zip}.pdf")
        else:
            c_input = st.text_input("Enter Access Code", type="password", placeholder="Enter code to unlock")
            if c_input == PRO_CODE:
                st.session_state.pro_unlocked = True
                st.rerun()
    with e2: 
        st.download_button("📊 Export CSV", data=row.to_frame().T.to_csv().encode('utf-8'), file_name=f"Data_{selected_zip}.csv")
    
    render_footer()

with tab_iq:
    st.header("YieldMap IQ Center")
    st.write("Metric Explanations & Knowledge Base...")
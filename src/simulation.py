import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import io

from fileProcessor import load
from aggregation import aggregation
from indexEngine import IndexEngine
from scenarios import ScenarioEngine, Scenarios

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Portfolio Dashboard",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens ─────────────────────────────────────────────────────────────
BG          = '#0D0F14'
SURFACE     = '#13161E'
SURFACE2    = '#1A1E2A'
BORDER      = '#252A38'
BORDER2     = '#2E3447'
TEXT        = '#E8ECF4'
TEXT_MUTED  = '#5A6278'
TEXT_DIM    = '#3D4460'
ACCENT      = '#4F8EF7'       # electric blue
ACCENT2     = '#7B5FD4'       # violet
GREEN       = '#2ECC8A'
AMBER       = '#F5A623'
RED         = '#E8455A'
AMORT_COLORS= ['#4F8EF7', '#2ECC8A', '#F5A623', '#E8455A']
GRID        = '#1E2230'

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0D0F14;
    color: #E8ECF4;
}

/* ── Main background ── */
.main, .block-container {
    background-color: #0D0F14 !important;
}

[data-testid="stHeader"] {
    display: none;
}
            

            

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0A0C11 !important;
    border-right: 1px solid #1E2230 !important;
}
[data-testid="stSidebar"] * { color: #E8ECF4 !important; }
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stFileUploader > div {
    background: #13161E !important;
    border: 1px solid #252A38 !important;
    border-radius: 8px !important;
}
            
[data-testid="stFileUploader"] {
    background-color: #13161E !important;
    border: 1px dashed #252A38 !important; /* גבול מקווקו למראה מודרני */
    border-radius: 12px !important;
    padding: 1rem;
}

[data-testid="stFileUploader"] section {
    background-color: #13161E !important;
    color: #E8ECF4 !important;
}

[data-testid="stFileUploader"] small {
    color: #5A6278 !important;
}

[data-testid="stFileUploader"] button {
    background-color: #1A1E2A !important;
    color: #4F8EF7 !important;
    border: 1px solid #252A38 !important;
    transition: all 0.3s ease;
}

[data-testid="stFileUploader"] button:hover {
    border-color: #4F8EF7 !important;
    background-color: #252A38 !important;
}

[data-testid="stFileUploaderIcon"] {
    color: #4F8EF7 !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] button {
    font-family: 'Syne', sans-serif !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #5A6278 !important;
    border: none !important;
    background: transparent !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #E8ECF4 !important;
    border-bottom: 2px solid #4F8EF7 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1E2230 !important;
    gap: 0 !important;
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    border: 1px solid #252A38 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    background: #13161E !important;
}
[data-testid="stDataFrame"] * { color: #E8ECF4 !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #4F8EF7 0%, #7B5FD4 100%) !important;
    color: #ffffff !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    border: none !important;
    border-radius: 8px !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: #13161E !important;
    color: #4F8EF7 !important;
    border: 1px solid #252A38 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}

/* ── Slider ── */
[data-testid="stSlider"] > div > div > div > div {
    background: #4F8EF7 !important;
}

/* ── Inputs ── */
.stSelectbox > div > div, .stFileUploader > div {
    background: #13161E !important;
    border: 1px solid #252A38 !important;
    border-radius: 8px !important;
    color: #E8ECF4 !important;
}
label, .stMarkdown p { color: #5A6278 !important; }

/* ── Metric card ── */
.metric-card {
    background: #13161E;
    border: 1px solid #1E2230;
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #4F8EF7, #7B5FD4);
    opacity: 0.6;
}
.metric-label {
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #3D4460;
    margin-bottom: 10px;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 40px;
    font-weight: 500;
    color: #E8ECF4;
    line-height: 1;
}
.metric-sub {
    font-size: 14px;
    color: #3D4460;
    margin-top: 6px;
    font-weight: 400;
}

/* ── Section header ── */
.section-header {
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #3D4460;
    margin: 32px 0 14px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #1E2230;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-header::before {
    content: '';
    display: inline-block;
    width: 3px; height: 12px;
    background: linear-gradient(180deg, #4F8EF7, #7B5FD4);
    border-radius: 2px;
}

/* ── Slider container ── */
.slider-container {
    background: #13161E;
    border: 1px solid #1E2230;
    border-radius: 12px;
    padding: 16px 24px 12px;
    margin-bottom: 24px;
}
.cutoff-badge {
    display: inline-block;
    background: rgba(79, 142, 247, 0.12);
    color: #4F8EF7;
    font-family: 'JetBrains Mono', monospace;
    font-size: 17px;
    font-weight: 500;
    padding: 3px 12px;
    border-radius: 20px;
    border: 1px solid rgba(79, 142, 247, 0.25);
    margin-left: 8px;
}

/* ── Page header ── */
.page-header {
    display: flex;
    align-items: baseline;
    gap: 14px;
    margin-bottom: 28px;
}
.page-title {
    font-size: 30px;
    font-weight: 800;
    color: #E8ECF4;
    letter-spacing: -0.02em;
}
.page-tag {
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4F8EF7;
    background: rgba(79,142,247,0.1);
    border: 1px solid rgba(79,142,247,0.2);
    padding: 3px 10px;
    border-radius: 4px;
}

/* ── Sidebar brand ── */
.sidebar-brand {
    font-size: 20px;
    font-weight: 800;
    color: #E8ECF4;
    letter-spacing: -0.01em;
}
.sidebar-sub {
    font-size: 15px;
    color: #3D4460;
    margin-top: 2px;
    font-family: 'JetBrains Mono', monospace;
}
.sidebar-divider {
    height: 1px;
    background: #1E2230;
    margin: 18px 0;
}
.filter-label {
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #3D4460;
    margin-bottom: 6px;
}

/* ── Warning / error override ── */
[data-testid="stAlert"] {
    background: rgba(232,69,90,0.08) !important;
    border: 1px solid rgba(232,69,90,0.25) !important;
    border-radius: 8px !important;
    color: #E8455A !important;
}

/* ── Caption ── */
.stCaption { color: #3D4460 !important; font-size: 15px !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #4F8EF7 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
LOAN_TYPES  = ['All', 'משכנתא דרגה 1', 'משכנתא דרגה 2', 'מימון יזמים',
               'מימון בעלי שליטה', 'אשראי קורפ', 'גישור', 'אחר']
AMORT_TYPES = ['All', 'שפיצר', 'קרן שווה', 'בלון', 'בולט']

with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">◈ PORTFOLIO</div>
        <div class="sidebar-sub">amortization · analytics</div>
        <div class="sidebar-divider"></div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("UPLOAD SCHEDULE FILE", type=["xlsx", "csv"])

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="filter-label">Filters</div>', unsafe_allow_html=True)
    loan_type_filter  = st.selectbox("LOAN TYPE",         LOAN_TYPES,  label_visibility="collapsed")
    st.markdown('<div style="font-size:15px;color:#3D4460;margin:-8px 0 6px;letter-spacing:0.08em;">LOAN TYPE</div>', unsafe_allow_html=True)
    amort_type_filter = st.selectbox("AMORTIZATION TYPE", AMORT_TYPES, label_visibility="collapsed")
    st.markdown('<div style="font-size:15px;color:#3D4460;margin:-8px 0 16px;letter-spacing:0.08em;">AMORTIZATION TYPE</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    run = st.button("▶  RUN ANALYSIS", use_container_width=True, type="primary")

# ── Session state ─────────────────────────────────────────────────────────────
for key in ['master', 'aggregator', 'engine', 'result', 'sim_results', 'sc_engine', 'sc_results']:
    if key not in st.session_state:
        st.session_state[key] = None

# ── Pipeline ──────────────────────────────────────────────────────────────────
if run and uploaded:
    with st.spinner("Processing schedules..."):
        master = load(uploaded)
        agg    = aggregation(master)

        criteria = {}
        if loan_type_filter  != 'All': criteria['Loan Type']         = loan_type_filter
        if amort_type_filter != 'All': criteria['Amortization Type'] = amort_type_filter

        try:
            result = agg.aggregate(**criteria)
        except ValueError as e:
            st.error(f"No schedules matched the selected filters: {e}")
            st.stop()

        st.session_state.master      = master
        st.session_state.aggregator  = agg
        st.session_state.engine      = IndexEngine()
        st.session_state.result      = result
        st.session_state.sim_results = None
        st.session_state.sc_engine  = ScenarioEngine(master)
        st.session_state.sc_results = None

elif run and not uploaded:
    st.sidebar.error("Please upload a file first.")


# ── Chart helpers (dark theme) ────────────────────────────────────────────────
def _fmt_y(ax):
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₪{x:,.0f}"))
    ax.tick_params(labelsize=12, colors='#5A6278')

def _fmt_x(ax):
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₪{x:,.0f}"))
    ax.tick_params(labelsize=12, colors='#5A6278')

def _style(ax, title):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, fontsize=14, fontweight='700', color=TEXT_MUTED,
                 pad=14, loc='left', fontfamily='monospace')
    ax.grid(axis='y', color=GRID, linewidth=0.6, alpha=1)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
        spine.set_linewidth(0.8)
    ax.tick_params(colors=TEXT_MUTED, labelsize=12)
    ax.xaxis.label.set_color(TEXT_MUTED)
    ax.yaxis.label.set_color(TEXT_MUTED)

def _metric(col, label, value, sub, accent=ACCENT):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{accent}">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

def _section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


# ── Dashboard ─────────────────────────────────────────────────────────────────
if st.session_state.result is not None:
    result = st.session_state.result
    master = st.session_state.master
    agg    = st.session_state.aggregator
    engine = st.session_state.engine

    filter_label = []
    if loan_type_filter  != 'All': filter_label.append(loan_type_filter)
    if amort_type_filter != 'All': filter_label.append(amort_type_filter)
    title = " · ".join(filter_label) if filter_label else "Full Portfolio"

    tag = "FILTERED VIEW" if filter_label else "ALL LOANS"
    st.markdown(f"""
        <div class="page-header">
            <span class="page-title">{title}</span>
            <span class="page-tag">{tag}</span>
        </div>
    """, unsafe_allow_html=True)

    tab_dashboard, tab_simulation, tab_scenarios = st.tabs(["  DASHBOARD  ", "  SIMULATION  ", "  IRRBB SCENARIOS  "])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — DASHBOARD
    # ════════════════════════════════════════════════════════════════════════
    with tab_dashboard:

        # Slider
        all_months = sorted(result['Month'].dt.to_pydatetime().tolist())
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:15px;font-weight:700;letter-spacing:0.12em;color:#3D4460;margin-bottom:6px;">TIME HORIZON CUTOFF</div>', unsafe_allow_html=True)
        cutoff_idx = st.slider("cutoff", 0, len(all_months)-1, len(all_months)-1,
                               format="%d", label_visibility="collapsed")
        cutoff_date = all_months[cutoff_idx]
        st.markdown(f'<span style="font-size:15px;color:#5A6278;">Showing up to</span><span class="cutoff-badge">{cutoff_date.strftime("%b %Y")}</span>',
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Apply cutoff
        result_cut = result[result['Month'] <= cutoff_date].copy()
        result_cut['Cumulative Repayment'] = result_cut['Total Monthly Repayment'].cumsum()

        # KPIs
        criteria_active = {}
        if loan_type_filter  != 'All': criteria_active['Loan Type']         = loan_type_filter
        if amort_type_filter != 'All': criteria_active['Amortization Type'] = amort_type_filter

        filtered_master = master.copy()
        for col, val in criteria_active.items():
            filtered_master = filtered_master[filtered_master[col] == val]

        disbursements   = filtered_master[filtered_master['Payment Number'] == 0]['Cash Flow'].sum()
        cfs             = [disbursements] + result_cut['Total Monthly Repayment'].tolist()
        total_repayment = result_cut['Total Monthly Repayment'].sum()
        num_loans       = agg.count_loans(**criteria_active)
        peak_month      = result_cut.loc[result_cut['Total Monthly Repayment'].idxmax(), 'Month'].strftime('%b %Y')

        try:
            irr_annual, _ = engine.calcIRR(cfs)
            irr_str = f"{irr_annual:.2%}"
        except Exception:
            irr_str = "N/A"

        _section("Portfolio KPIs")
        c1, c2, c3, c4, c5 = st.columns(5)
        _metric(c1, "Annual IRR",      irr_str,                    "up to cutoff date",    ACCENT)
        _metric(c2, "Total Repayment", f"₪{total_repayment:,.0f}", "up to cutoff date",    TEXT)
        _metric(c3, "Loans",           str(num_loans),             "matched schedules",    ACCENT2)
        _metric(c4, "Active Periods",  str(len(result_cut)),       "months with cashflow", TEXT_MUTED)
        _metric(c5, "Peak Month",      peak_month,                 "highest single month", AMBER)

        # Charts — stacked vertically, full width
        _section("Cash Flow Analysis")

        fig, ax = plt.subplots(figsize=(14, 5))
        fig.patch.set_facecolor(SURFACE)
        width = max(8, 500 / max(len(result_cut), 1))
        ax.bar(result_cut['Month'], result_cut['Total Monthly Repayment'],
               color=ACCENT, width=width, alpha=0.85, zorder=3)
        if cutoff_idx < len(all_months) - 1:
            ax.axvline(cutoff_date, color=AMBER, linewidth=1.4, linestyle='--', alpha=0.7, zorder=4)
        _style(ax, 'MONTHLY CASH FLOW')
        ax.set_xlabel('Month', fontsize=13); ax.set_ylabel('Amount (₪)', fontsize=13)
        ax.tick_params(axis='x', rotation=45, labelsize=11)
        _fmt_y(ax); fig.tight_layout(); st.pyplot(fig); plt.close()

        fig, ax = plt.subplots(figsize=(14, 5))
        fig.patch.set_facecolor(SURFACE)
        ax.plot(result['Month'], result['Cumulative Repayment'],
                color=BORDER2, linewidth=1.5, zorder=2)
        ax.plot(result_cut['Month'], result_cut['Cumulative Repayment'],
                color=GREEN, linewidth=2.5, marker='o', markersize=3, zorder=3)
        ax.fill_between(result_cut['Month'], result_cut['Cumulative Repayment'],
                        alpha=0.07, color=GREEN, zorder=2)
        if cutoff_idx < len(all_months) - 1:
            ax.axvline(cutoff_date, color=AMBER, linewidth=1.4, linestyle='--', alpha=0.7, zorder=4)
        _style(ax, 'CUMULATIVE REPAYMENT')
        ax.set_xlabel('Month', fontsize=13); ax.set_ylabel('Cumulative (₪)', fontsize=13)
        ax.tick_params(axis='x', rotation=45, labelsize=11)
        _fmt_y(ax); fig.tight_layout(); st.pyplot(fig); plt.close()

        # Charts — Portfolio Breakdown
        _section("Portfolio Breakdown")
        df_all = filtered_master[
            (filtered_master['Payment Number'] != 0) &
            (filtered_master['Date'] <= cutoff_date)
        ]

        by_type = df_all.groupby('Loan Type')['Total Monthly Repayment'].sum().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(14, 5)); fig.patch.set_facecolor(SURFACE)
        palette = [ACCENT, ACCENT2, GREEN, AMBER, RED, '#C0C0C0', '#80D0FF']
        bars = ax.barh(by_type.index, by_type.values,
                       color=palette[:len(by_type)], height=0.55, alpha=0.9, zorder=3)
        _style(ax, 'BY LOAN TYPE'); ax.set_xlabel('Total Repayment (₪)', fontsize=13)
        ax.grid(axis='x', color=GRID, linewidth=0.6); ax.grid(axis='y', visible=False)
        _fmt_x(ax)
        for bar, val in zip(bars, by_type.values):
            ax.text(val*1.01, bar.get_y()+bar.get_height()/2,
                    f"₪{val:,.0f}", va='center', fontsize=11, color=TEXT_MUTED)
        fig.tight_layout(); st.pyplot(fig); plt.close()

        by_amort = df_all.groupby('Amortization Type')['Total Monthly Repayment'].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(14, 5)); fig.patch.set_facecolor(SURFACE)
        bars2 = ax.bar(by_amort.index, by_amort.values,
                       color=AMORT_COLORS[:len(by_amort)], width=0.45, alpha=0.9, zorder=3)
        _style(ax, 'BY AMORTIZATION TYPE'); ax.set_ylabel('Total Repayment (₪)', fontsize=13)
        _fmt_y(ax)
        for bar, val in zip(bars2, by_amort.values):
            ax.text(bar.get_x()+bar.get_width()/2, val*1.015,
                    f"₪{val:,.0f}", ha='center', fontsize=11, color=TEXT_MUTED)
        fig.tight_layout(); st.pyplot(fig); plt.close()

        # Table
        _section("Aggregated Schedule")
        disp = result_cut.copy()
        disp['Month'] = disp['Month'].dt.strftime('%b %Y')
        for c in ['Total Monthly Repayment', 'Cumulative Repayment']:
            disp[c] = disp[c].apply(lambda x: f"₪{x:,.0f}")
        st.dataframe(disp, use_container_width=True, hide_index=True)

        # Export
        _section("Export")
        buf = io.BytesIO()
        result_cut.to_excel(buf, index=False, engine='openpyxl'); buf.seek(0)
        st.download_button("⬇  Download as Excel", buf,
                           file_name=f"portfolio_{title.replace(' · ','_')}_{cutoff_date.strftime('%Y%m')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — SIMULATION
    # ════════════════════════════════════════════════════════════════════════
    with tab_simulation:
        st.markdown("""
            <div class="page-header" style="margin-top:8px;">
                <span class="page-title">Loan-Level Simulation</span>
                <span class="page-tag">INDEX ENGINE</span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<p style="color:#3D4460;font-size:15px;margin-bottom:24px;font-family:\'JetBrains Mono\',monospace;">Fill in NOI parameters per loan → Run Simulation → Review risk indices</p>', unsafe_allow_html=True)

        # Build params table
        loan_summary = (
            master.groupby('Loan ID')
            .apply(lambda g: pd.Series({
                'Client':         g['Client'].iloc[0],
                'Loan Amount':    abs(g['Cash Flow'].iloc[0]),
                'Collateral (₪)': g['Collateral Value'].iloc[0],
            }))
            .reset_index()
        )
        loan_summary['pgi']  = 0.0
        loan_summary['vl']   = 0.0
        loan_summary['opex'] = 0.0

        _section("Input Parameters")
        st.caption("Collateral loaded from appraiser valuation · Fill in: PGI = monthly gross income | VL = vacancy loss | OPEX = operating expenses")

        edited = st.data_editor(
            loan_summary,
            use_container_width=True, hide_index=True,
            disabled=['Loan ID', 'Client', 'Loan Amount', 'Collateral (₪)'],
            column_config={
                'Collateral (₪)': st.column_config.NumberColumn('Collateral (₪)', format="₪%d"),
                'pgi':            st.column_config.NumberColumn('PGI (₪/mo)',     min_value=0, format="₪%d"),
                'vl':             st.column_config.NumberColumn('Vacancy Loss',   min_value=0, format="₪%d"),
                'opex':           st.column_config.NumberColumn('OPEX (₪/mo)',    min_value=0, format="₪%d"),
                'Loan Amount':    st.column_config.NumberColumn('Loan Amount (₪)',format="₪%d"),
            },
        )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        if st.button("◈  RUN SIMULATION", type="primary", use_container_width=True):
            with st.spinner("Computing indices..."):
                params = {
                    str(row['Loan ID']): {
                        'pgi':  row['pgi'],
                        'vl':   row['vl'],
                        'opex': row['opex'],
                    }
                    for _, row in edited.iterrows()
                }
                sim_results = engine.calcAll(master, params)

            if sim_results.empty:
                st.warning("No rows could be calculated. Check that the file contains a Collateral Value column.")
            else:
                summary = {
                    'num_loans':          len(sim_results),
                    'avg_LTV':            round(sim_results['Avg LTV (%)'].mean(), 2),
                    'avg_DSCR':           round(sim_results['DSCR'].mean(), 3),
                    'avg_Duration':       round(sim_results['Duration (months)'].mean(), 2),
                    'loans_above_1_DSCR': int((sim_results['DSCR'] >= 1).sum()),
                    'loans_below_1_DSCR': int((sim_results['DSCR'] <  1).sum()),
                    'high_ltv_loans':     int((sim_results['Avg LTV (%)'] > 75).sum()),
                }
                st.session_state.sim_results = (sim_results, summary)

        if st.session_state.sim_results is not None:
            sim_results, summary = st.session_state.sim_results

            _section("Portfolio Summary")
            s1, s2, s3, s4, s5 = st.columns(5)
            _metric(s1, "Loans Simulated",  str(summary['num_loans']),          "with params set",       ACCENT)
            _metric(s2, "Avg LTV",          f"{summary['avg_LTV']:.1f}%",       "loan-to-value",         TEXT)
            _metric(s3, "Avg DSCR",         f"{summary['avg_DSCR']:.3f}",       "debt service coverage", GREEN)
            _metric(s4, "DSCR < 1",         str(summary['loans_below_1_DSCR']), "at-risk loans",         RED)
            _metric(s5, "LTV > 75%",        str(summary['high_ltv_loans']),     "high exposure",         AMBER)

            _section("Results by Loan")

            def _color_dscr(val):
                if val is None: return ''
                if val < 1.0:   return f'color: {RED}; font-weight: 600'
                if val < 1.25:  return f'color: {AMBER}; font-weight: 600'
                return f'color: {GREEN}; font-weight: 600'

            def _color_ltv(val):
                if val is None: return ''
                if val > 85: return f'color: {RED}; font-weight: 600'
                if val > 75: return f'color: {AMBER}; font-weight: 600'
                return f'color: {GREEN}; font-weight: 600'

            styled = (
                sim_results.style
                .format({
                    'Loan Amount':       '₪{:,.0f}',
                    'Avg LTV (%)':       '{:.1f}%',
                    'Min LTV (%)':       '{:.1f}%',
                    'Max LTV (%)':       '{:.1f}%',
                    'DSCR':              '{:.3f}',
                    'Duration (months)': '{:.1f}',
                    'IRR (annual)':      lambda x: f"{x:.2%}" if x is not None else "N/A",
                })
                .applymap(_color_dscr, subset=['DSCR'])
                .applymap(_color_ltv,  subset=['Avg LTV (%)', 'Min LTV (%)', 'Max LTV (%)'])
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)

            # Simulation charts — stacked vertically, full width
            _section("Index Visualization")

            fig, ax = plt.subplots(figsize=(14, 5)); fig.patch.set_facecolor(SURFACE)
            colors_ltv = [RED if v > 85 else AMBER if v > 75 else GREEN
                          for v in sim_results['Avg LTV (%)']]
            ax.barh(sim_results['Loan ID'], sim_results['Avg LTV (%)'],
                    color=colors_ltv, height=0.55, alpha=0.9, zorder=3)
            ax.axvline(75, color=AMBER, linewidth=1.2, linestyle='--', alpha=0.6)
            ax.axvline(85, color=RED,   linewidth=1.2, linestyle='--', alpha=0.6)
            _style(ax, 'AVG LTV BY LOAN (%)')
            ax.set_xlabel('Avg LTV (%)', fontsize=13)
            ax.grid(axis='x', color=GRID, linewidth=0.6); ax.grid(axis='y', visible=False)
            fig.tight_layout(); st.pyplot(fig); plt.close()

            fig, ax = plt.subplots(figsize=(14, 5)); fig.patch.set_facecolor(SURFACE)
            colors_dscr = [RED if v < 1.0 else AMBER if v < 1.25 else GREEN
                           for v in sim_results['DSCR']]
            ax.barh(sim_results['Loan ID'], sim_results['DSCR'],
                    color=colors_dscr, height=0.55, alpha=0.9, zorder=3)
            ax.axvline(1.0,  color=RED,   linewidth=1.2, linestyle='--', alpha=0.6)
            ax.axvline(1.25, color=AMBER, linewidth=1.2, linestyle='--', alpha=0.6)
            _style(ax, 'DSCR BY LOAN')
            ax.set_xlabel('DSCR', fontsize=13)
            ax.grid(axis='x', color=GRID, linewidth=0.6); ax.grid(axis='y', visible=False)
            fig.tight_layout(); st.pyplot(fig); plt.close()

            _section("Export")
            buf2 = io.BytesIO()
            sim_results.to_excel(buf2, index=False, engine='openpyxl'); buf2.seek(0)
            st.download_button("⬇  Download Simulation Results", buf2,
                               file_name="simulation_results.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — IRRBB SCENARIOS
    # ════════════════════════════════════════════════════════════════════════
    with tab_scenarios:
        st.markdown("""
            <div class="page-header" style="margin-top:8px;">
                <span class="page-title">IRRBB Scenario Analysis</span>
                <span class="page-tag">INTEREST RATE RISK</span>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('<p style="color:#3D4460;font-size:15px;margin-bottom:20px;">6 Basel/EBA standard shocks · NII horizon 12M · EVE full-lifetime NPV</p>', unsafe_allow_html=True)

        sc_engine = st.session_state.sc_engine

        # ── Custom scenario row ──
        _section("Custom Scenario")
        ci1, ci2, ci3 = st.columns([2, 2, 3])
        with ci1:
            custom_short = st.number_input(
                "Short-end shock (bp)", value=0, step=25, min_value=-500, max_value=500,
                key='sc_short')
        with ci2:
            custom_long = st.number_input(
                "Long-end shock (bp)", value=0, step=25, min_value=-500, max_value=500,
                key='sc_long')
        with ci3:
            st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
            include_custom = st.checkbox("Include custom in run", value=False, key='sc_custom_chk')

        # ── Run button ──
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("◈  RUN ALL SCENARIOS", type="primary", use_container_width=True):
            with st.spinner("Computing NII & EVE across all scenarios..."):
                scenarios_to_run = Scenarios.all_standard()
                if include_custom:
                    scenarios_to_run.append(
                        Scenarios.Custom(custom_short, custom_long))

                summary_rows = []
                detail_rows  = {}
                for sc in scenarios_to_run:
                    res = sc_engine.apply(sc)
                    summary_rows.append({
                        'Scenario':         res['scenario_name'],
                        'Description':      res['description'],
                        'Short (bp)':       res['short_shock_bp'],
                        'Long (bp)':        res['long_shock_bp'],
                        'NII Base (₪)':     res['nii_base'],
                        'NII Shocked (₪)':  res['nii_shocked'],
                        'ΔNII (₪)':         res['nii_delta'],
                        'ΔNII (%)':         res['nii_delta'] / res['nii_base'] * 100
                                            if res['nii_base'] else 0,
                        'EVE Base (₪)':     res['eve_base'],
                        'EVE Shocked (₪)':  res['eve_shocked'],
                        'ΔEVE (₪)':         res['eve_delta'],
                        'ΔEVE (%)':         res['eve_delta'] / res['eve_base'] * 100
                                            if res['eve_base'] else 0,
                    })
                    detail_rows[res['scenario_name']] = res['loan_details']

                st.session_state.sc_results = (
                    pd.DataFrame(summary_rows), detail_rows)

        # ── Results ──
        if st.session_state.sc_results is not None:
            sc_summary, sc_details = st.session_state.sc_results

            # ── Portfolio-level KPIs (worst cases) ──
            _section("Worst-Case Portfolio Exposure")
            worst_nii = sc_summary.loc[sc_summary['ΔNII (₪)'].idxmin()]
            worst_eve = sc_summary.loc[sc_summary['ΔEVE (₪)'].idxmin()]
            var_loans = int(master['Changing Interest'].sum() /
                            master.groupby('Loan ID').ngroups
                            * master['Loan ID'].nunique())                         if 'Changing Interest' in master.columns else 0

            k1, k2, k3, k4 = st.columns(4)
            _metric(k1, "Worst ΔNII",
                    f"₪{worst_nii['ΔNII (₪)']:,.0f}",
                    worst_nii['Scenario'],
                    RED if worst_nii['ΔNII (₪)'] < 0 else GREEN)
            _metric(k2, "Worst ΔEVE",
                    f"₪{worst_eve['ΔEVE (₪)']:,.0f}",
                    worst_eve['Scenario'],
                    RED if worst_eve['ΔEVE (₪)'] < 0 else GREEN)
            _metric(k3, "Variable Loans",
                    str(master['Changing Interest'].groupby(
                        master['Loan ID']).first().sum()
                        if 'Changing Interest' in master.columns else 'N/A'),
                    "NII-sensitive to short shock", ACCENT)
            _metric(k4, "NII Horizon",
                    "12 months", "Basel IRRBB standard", TEXT_MUTED)

            # ── Summary table ──
            _section("Scenario Summary — NII & EVE")

            def _fmt_delta(val, pct):
                arrow = "▲" if val >= 0 else "▼"
                color = GREEN if val >= 0 else RED
                return f'color: {color}; font-weight: 600'

            styled_summary = (
                sc_summary.style
                .format({
                    'NII Base (₪)':    '₪{:,.0f}',
                    'NII Shocked (₪)': '₪{:,.0f}',
                    'ΔNII (₪)':        '₪{:,.0f}',
                    'ΔNII (%)':        '{:+.1f}%',
                    'EVE Base (₪)':    '₪{:,.0f}',
                    'EVE Shocked (₪)': '₪{:,.0f}',
                    'ΔEVE (₪)':        '₪{:,.0f}',
                    'ΔEVE (%)':        '{:+.1f}%',
                })
                .applymap(lambda v: f'color: {GREEN}; font-weight:600'
                          if isinstance(v, (int,float)) and v >= 0
                          else (f'color: {RED}; font-weight:600'
                                if isinstance(v, (int,float)) and v < 0 else ''),
                          subset=['ΔNII (₪)', 'ΔNII (%)', 'ΔEVE (₪)', 'ΔEVE (%)'])
            )
            st.dataframe(styled_summary, use_container_width=True, hide_index=True)

            # ── Charts — stacked vertically, full width ──
            _section("NII & EVE Sensitivity — All Scenarios")

            fig, ax = plt.subplots(figsize=(14, 5))
            fig.patch.set_facecolor(SURFACE)
            sc_names = sc_summary['Scenario'].tolist()
            nii_deltas = sc_summary['ΔNII (₪)'].tolist()
            colors_nii = [GREEN if v >= 0 else RED for v in nii_deltas]
            bars = ax.barh(sc_names, nii_deltas,
                           color=colors_nii, height=0.55, alpha=0.9, zorder=3)
            ax.axvline(0, color=TEXT_MUTED, linewidth=0.8, alpha=0.5)
            _style(ax, 'ΔNII BY SCENARIO (₪)')
            ax.set_xlabel('ΔNII (₪)', fontsize=13)
            ax.grid(axis='x', color=GRID, linewidth=0.6)
            ax.grid(axis='y', visible=False)
            _fmt_x(ax)
            fig.tight_layout(); st.pyplot(fig); plt.close()

            fig, ax = plt.subplots(figsize=(14, 5))
            fig.patch.set_facecolor(SURFACE)
            eve_deltas = sc_summary['ΔEVE (₪)'].tolist()
            colors_eve = [GREEN if v >= 0 else RED for v in eve_deltas]
            ax.barh(sc_names, eve_deltas,
                    color=colors_eve, height=0.55, alpha=0.9, zorder=3)
            ax.axvline(0, color=TEXT_MUTED, linewidth=0.8, alpha=0.5)
            _style(ax, 'ΔEVE BY SCENARIO (₪)')
            ax.set_xlabel('ΔEVE (₪)', fontsize=13)
            ax.grid(axis='x', color=GRID, linewidth=0.6)
            ax.grid(axis='y', visible=False)
            _fmt_x(ax)
            fig.tight_layout(); st.pyplot(fig); plt.close()

            # ── Loan-level drill-down ──
            _section("Loan-Level Drill-Down")
            selected_sc = st.selectbox(
                "Select scenario to inspect",
                options=list(sc_details.keys()),
                key='sc_drill_select')

            if selected_sc and selected_sc in sc_details:
                detail_df = sc_details[selected_sc]

                def _color_delta(val):
                    if not isinstance(val, (int, float)): return ''
                    return (f'color: {GREEN}; font-weight:600' if val >= 0
                            else f'color: {RED}; font-weight:600')

                styled_detail = (
                    detail_df.style
                    .format({
                        'NII Base (₪)':    '₪{:,.0f}',
                        'NII Shocked (₪)': '₪{:,.0f}',
                        'ΔNII (₪)':        '₪{:,.0f}',
                        'EVE Base (₪)':    '₪{:,.0f}',
                        'EVE Shocked (₪)': '₪{:,.0f}',
                        'ΔEVE (₪)':        '₪{:,.0f}',
                    })
                    .applymap(_color_delta,
                              subset=['ΔNII (₪)', 'ΔEVE (₪)'])
                )
                st.dataframe(styled_detail, use_container_width=True, hide_index=True)

            # ── Export ──
            _section("Export")
            buf_sc = io.BytesIO()
            with pd.ExcelWriter(buf_sc, engine='openpyxl') as writer:
                sc_summary.to_excel(writer, sheet_name='Summary', index=False)
                for sc_name, df_detail in sc_details.items():
                    sheet_name = sc_name[:31].replace('/', '-').replace(':', '')
                    df_detail.to_excel(writer, sheet_name=sheet_name, index=False)
            buf_sc.seek(0)
            st.download_button(
                "⬇  Download Scenario Results",
                buf_sc,
                file_name="irrbb_scenarios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)


else:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;
                justify-content:center;height:65vh;text-align:center;">
        <div style="font-size:48px;margin-bottom:20px;opacity:0.15;">◈</div>
        <div style="font-size:20px;font-weight:800;color:#E8ECF4;margin-bottom:8px;letter-spacing:-0.02em;">
            Portfolio Dashboard
        </div>
        <div style="font-size:14px;color:#3D4460;max-width:320px;line-height:1.8;
                    font-family:'JetBrains Mono',monospace;letter-spacing:0.04em;">
            Upload <code style="color:#4F8EF7">AS_ALL.xlsx</code> in the sidebar<br>
            choose your filters → Run Analysis
        </div>
    </div>
    """, unsafe_allow_html=True)

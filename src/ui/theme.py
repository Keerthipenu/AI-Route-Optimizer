CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {
  --rf-bg: #101210; --rf-panel: #171a17; --rf-panel-2: #1c201b;
  --rf-line: #30362d; --rf-text: #eef1e9; --rf-muted: #929b8c;
  --rf-accent: #c7f464; --rf-orange: #f39a55;
}
.stApp { background: var(--rf-bg); color: var(--rf-text); font-family: 'Manrope', sans-serif; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #121512; border-right: 1px solid var(--rf-line); }
[data-testid="stSidebar"] hr { border-color: var(--rf-line); }
h1, h2, h3 { letter-spacing: -.035em !important; }
.rf-kicker, .rf-mono, [data-testid="stMetricLabel"] { font-family: 'DM Mono', monospace !important; }
.rf-kicker { color: var(--rf-accent); font-size: .72rem; letter-spacing: .17em; text-transform: uppercase; }
.rf-brand { display:flex; align-items:center; gap:.75rem; margin:.25rem 0 1.5rem; }
.rf-mark { width:34px; height:34px; display:grid; place-items:center; border:1px solid var(--rf-accent); color:var(--rf-accent); font-weight:800; }
.rf-wordmark { font-weight:800; letter-spacing:.16em; font-size:.9rem; }
.rf-submark { color:var(--rf-muted); font-size:.61rem; letter-spacing:.07em; }
.rf-hero { border-top:1px solid var(--rf-line); border-bottom:1px solid var(--rf-line); padding:1.2rem 0; margin-bottom:1.4rem; }
.rf-hero h1 { margin:.25rem 0 .35rem; font-size:clamp(2rem,4vw,3.5rem); line-height:1; }
.rf-hero p { color:var(--rf-muted); margin:0; }
.rf-panel { background:var(--rf-panel); border:1px solid var(--rf-line); padding:1rem 1.1rem; }
.rf-callout { border-left:3px solid var(--rf-accent); background:var(--rf-panel); padding:1rem 1.15rem; color:#cbd1c6; }
.rf-stop { display:grid; grid-template-columns:2.1rem 1fr auto; gap:.75rem; padding:.65rem 0; border-bottom:1px solid #292e27; align-items:center; }
.rf-stop:last-child { border-bottom:0; }
.rf-stop-num { font-family:'DM Mono',monospace; color:var(--rf-accent); font-size:.72rem; }
.rf-stop-name { font-weight:600; font-size:.9rem; }
.rf-stop-meta { color:var(--rf-muted); font-size:.72rem; }
.rf-stop-distance { font-family:'DM Mono',monospace; font-size:.75rem; color:#c3c9be; }
.rf-section { font-family:'DM Mono',monospace; letter-spacing:.13em; text-transform:uppercase; font-size:.7rem; color:#a7afa2; margin:.8rem 0; }
.rf-note { color:var(--rf-muted); font-size:.78rem; line-height:1.55; }
.rf-rule { height:1px; background:var(--rf-line); margin:1.25rem 0; }
div[data-testid="stMetric"] { background:transparent; border-top:1px solid var(--rf-line); padding-top:.75rem; }
div[data-testid="stMetricValue"] { font-weight:600; }
.stButton > button, .stDownloadButton > button { border-radius:0 !important; border:1px solid var(--rf-accent) !important; }
.stButton > button[kind="primary"] { background:var(--rf-accent) !important; color:#101210 !important; font-weight:800; }
div[data-baseweb="select"] > div, input, textarea { border-radius:0 !important; }
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] { border:1px solid var(--rf-line); }
.stTabs [data-baseweb="tab-list"] { gap:1.5rem; border-bottom:1px solid var(--rf-line); }
.stTabs [data-baseweb="tab"] { border-radius:0; padding-left:0; padding-right:0; }
.stTabs [aria-selected="true"] { color:var(--rf-accent) !important; }
@media (max-width: 768px) { .rf-hero h1 { font-size:2.25rem; } .block-container { padding-top:1.5rem; } }
</style>
"""


def inject_theme(st) -> None:
    st.markdown(CSS, unsafe_allow_html=True)

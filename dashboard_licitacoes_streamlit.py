"""
Ampla — Radar de Licitações  v3
================================
Página principal: visão geral e gráficos.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import traceback
import json
from io import BytesIO
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    import gspread
    GSPREAD_OK = True
except ImportError:
    GSPREAD_OK = False

# ── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ampla — Radar de Licitações",
    page_icon="https://www.ampla.com.br/wp-content/uploads/2023/01/cropped-favicon-192x192.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta ────────────────────────────────────────────────────────────────────
AZUL        = "#001FFF"
AZUL_ESC    = "#0016CC"
AZUL_MID    = "#4d6bff"
AZUL_LIGHT  = "#e8ebff"
BRANCO      = "#FFFFFF"
BG          = "#0f0f13"
SURFACE     = "#18181e"
SURFACE2    = "#22222c"
BORDA       = "#2e2e3d"
TEXTO       = "#f0f0f8"
MUTED       = "#8888aa"
VERDE       = "#00c48c"
AMARELO     = "#f59e0b"
VERMELHO    = "#ef4444"

FONTE_CORES = {
    "PNCP":           AZUL,
    "Querido Diário": AZUL_MID,
    "BLL":            AMARELO,
    "Licitações-e":   VERDE,
}

SCORE_WEIGHTS = {
    "agência de publicidade":    40,
    "campanha publicitária":     35,
    "criação publicitária":      35,
    "veiculação de mídia":       30,
    "produção audiovisual":      28,
    "comunicação social":        25,
    "assessoria de comunicação": 25,
    "serviços de comunicação":   22,
    "publicidade":               20,
    "propaganda":                18,
    "mídia exterior":            18,
    "inserção televisiva":       18,
    "inserção de mídia":         16,
    "outdoor":                   14,
    "busdoor":                   14,
    "mídia":                     12,
    "marketing":                 10,
    "veiculação":                 8,
    "relações públicas":          8,
    "anúncio":                    6,
}

NOME_PLANILHA    = "Data Licitacoes"
NOME_ABA         = "Página1"
CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

LOGO_SVG = '<img src="https://www.ampla.com.br/wp-content/uploads/2022/12/logo-ampla.svg" height="105" style="margin-bottom:15px;margin-top:5px;">'
LOGO_SVG_BRANCA = '<img src="https://handson.tec.br/static/img/logo/logo-branca.png" height="50">'

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Space Grotesk', sans-serif !important; background-color: {BG} !important; color: {TEXTO}; }}
.stApp {{ background-color: {BG} !important; }}
.block-container {{ background-color: {BG} !important; padding-top: 1.5rem !important; }}
.stApp > header, [data-testid="stHeader"] {{ background: transparent !important; }}
p, span, div, label {{ font-family: 'Space Grotesk', sans-serif !important; }}
h1, h2, h3, h4 {{ font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; color: {TEXTO} !important; }}
[data-baseweb="select"] svg {{ fill: {MUTED} !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] svg {{ fill: white !important; }}
section[data-testid="stSidebar"] {{ background: {AZUL} !important; border-right: none !important; }}
section[data-testid="stSidebar"] * {{ color: rgba(255,255,255,0.9) !important; font-family: 'Space Grotesk', sans-serif !important; }}
section[data-testid="stSidebar"] .stSelectbox label, section[data-testid="stSidebar"] .stSlider label, section[data-testid="stSidebar"] .stTextInput label {{ color: rgba(255,255,255,0.6) !important; font-size: 10px !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; font-weight: 600 !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] {{ background: rgba(255,255,255,0.12) !important; border-radius: 8px !important; border: 1px solid rgba(255,255,255,0.22) !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] * {{ color: white !important; background: transparent !important; }}
section[data-testid="stSidebar"] input {{ background: rgba(255,255,255,0.12) !important; border: 1px solid rgba(255,255,255,0.22) !important; border-radius: 8px !important; color: white !important; }}
section[data-testid="stSidebar"] input::placeholder {{ color: rgba(255,255,255,0.35) !important; }}
section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.18) !important; }}
[data-testid="metric-container"] {{ background: {SURFACE} !important; border: 1px solid {BORDA} !important; border-radius: 14px !important; padding: 1.1rem 1.3rem !important; border-top: 3px solid {AZUL} !important; }}
[data-testid="stMetricLabel"] {{ font-size: 10px !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; color: {MUTED} !important; font-weight: 600 !important; }}
[data-testid="stMetricValue"] {{ font-weight: 700 !important; font-size: 1.85rem !important; color: {AZUL} !important; letter-spacing: -0.02em !important; }}
[data-testid="stMetricDelta"] {{ font-size: 11px !important; color: {MUTED} !important; }}
[data-testid="stMetricDelta"] svg {{ display: none !important; }}
.stButton > button {{ background: {AZUL} !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; font-family: 'Space Grotesk', sans-serif !important; }}
.stButton > button:hover {{ opacity: 0.82 !important; }}
[data-baseweb="select"] {{ background: {SURFACE2} !important; border-radius: 8px !important; border: 1px solid {BORDA} !important; }}
[data-baseweb="popover"] ul {{ background: {SURFACE2} !important; }}
[data-baseweb="popover"] li {{ background: {SURFACE2} !important; color: {TEXTO} !important; }}
[data-baseweb="popover"] li:hover {{ background: {BORDA} !important; }}
.stTextInput input {{ background: {SURFACE2} !important; border: 1px solid {BORDA} !important; border-radius: 8px !important; color: {TEXTO} !important; }}
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDA}; border-radius: 3px; }}
hr {{ border-color: {BORDA} !important; }}
.section-header {{ font-size: 10px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.12em !important; color: {MUTED} !important; margin-bottom: 0.75rem !important; }}
.status-ok {{ display: inline-flex; align-items: center; gap: 6px; background: rgba(0,31,255,0.12); color: {AZUL}; border: 1px solid rgba(0,31,255,0.25); border-radius: 20px; padding: 4px 12px; font-size: 11px; font-weight: 600; }}
.dot-ok {{ width: 6px; height: 6px; background: {AZUL}; border-radius: 50%; animation: blink 2s ease-in-out infinite; }}
@keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
</style>
""", unsafe_allow_html=True)


# ── Funções ───────────────────────────────────────────────────────────────────

def calcular_score(row) -> int:
    texto = f"{row.get('objeto','') or ''} {row.get('palavras_encontradas','') or ''}".lower()
    score = sum(w for kw, w in SCORE_WEIGHTS.items() if kw in texto)
    mod = str(row.get("modalidade", "") or "").lower()
    if "concurso"       in mod: score += 15
    elif "concorrência" in mod: score += 8
    elif "pregão"       in mod: score += 5
    if str(row.get("fonte", "")) == "PNCP": score += 5
    try:
        if float(row.get("valor_estimado") or 0) > 0: score += 5
    except Exception:
        pass
    return min(int(score), 99)

def score_label(s): return "🟢 Alto" if s >= 70 else "🟡 Médio" if s >= 50 else "🔴 Baixo"
def score_color(s): return VERDE if s >= 70 else AMARELO if s >= 50 else VERMELHO


# ── Google Sheets ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def carregar_do_sheets(_gc, planilha_nome, aba_nome):
    planilha = _gc.open(planilha_nome)
    ws = planilha.worksheet(aba_nome)
    dados = ws.get_all_records(default_blank="")
    if not dados:
        return pd.DataFrame()
    df = pd.DataFrame(dados).fillna("")
    df["score"]      = df.apply(calcular_score, axis=1)
    df["prioridade"] = df["score"].apply(score_label)
    df["valor_num"]  = pd.to_numeric(df.get("valor_estimado", ""), errors="coerce").fillna(0)
    if "data_publicacao"   in df.columns: df["data_pub"] = pd.to_datetime(df["data_publicacao"],   errors="coerce")
    if "data_encerramento" in df.columns: df["data_enc"] = pd.to_datetime(df["data_encerramento"], errors="coerce")
    return df.sort_values("score", ascending=False).reset_index(drop=True)


def conectar_sheets():
    if "gc" not in st.session_state:
        if not GSPREAD_OK:
            raise RuntimeError("gspread não instalado")

        if "credentials" in st.secrets:
            raw = dict(st.secrets["credentials"])
            raw["private_key"] = raw["private_key"].replace("\\n", "\n")
        elif CREDENTIALS_PATH.exists():
            with open(CREDENTIALS_PATH) as f:
                raw = json.load(f)
        else:
            raise FileNotFoundError("Credenciais não encontradas nos Secrets nem localmente.")

        st.session_state["gc"] = gspread.service_account_from_dict(raw)

    return st.session_state["gc"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(LOGO_SVG_BRANCA, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.55);margin-bottom:8px'>Fonte de dados</div>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        st.markdown(f"<div style='font-size:12px;color:rgba(255,255,255,0.85)'>📊 {NOME_PLANILHA}</div>", unsafe_allow_html=True)
    with col_s2:
        if st.button("↻", help="Recarregar dados"):
            st.cache_data.clear()
            st.rerun()
    st.markdown("---")
    st.markdown("<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.55);margin-bottom:12px'>Filtros</div>", unsafe_allow_html=True)
    filtros_ph = st.empty()


# ── Conectar e carregar ───────────────────────────────────────────────────────
sheets_ok  = False
sheets_err = None
sheets_tb  = None
df_raw     = pd.DataFrame()

with st.spinner("Conectando ao Google Sheets..."):
    try:
        gc     = conectar_sheets()
        df_raw = carregar_do_sheets(gc, NOME_PLANILHA, NOME_ABA)
        sheets_ok = True
    except Exception as e:
        sheets_err = str(e)
        sheets_tb  = traceback.format_exc()

if not sheets_ok:
    st.error(f"❌ Erro ao conectar: {sheets_err}")
    st.code(sheets_tb, language="python")
    if "credentials" in st.secrets:
        raw = dict(st.secrets["credentials"])
        st.info(f"✅ Secret [credentials] encontrado\n\n**client_email:** {raw.get('client_email')}\n\n**private_key começa com:** {raw.get('private_key','')[:60]}")
    else:
        st.warning("❌ Secret [credentials] NÃO encontrado!")
    st.stop()

if df_raw.empty:
    st.warning("Planilha conectada, mas sem dados. Rode o buscador para popular a planilha.")
    st.stop()

st.session_state["df_raw"] = df_raw


# ── Filtros (sidebar) ─────────────────────────────────────────────────────────
with filtros_ph.container():
    busca     = st.text_input("🔍 Buscar", placeholder="publicidade, mídia...")
    ufs       = ["Todos"] + sorted([u for u in df_raw["uf"].dropna().unique() if u])
    uf_sel    = st.selectbox("📍 Estado", ufs)
    fontes    = ["Todas"] + sorted([f for f in df_raw["fonte"].dropna().unique() if f])
    fonte_sel = st.selectbox("📰 Fonte", fontes)
    score_min = st.slider("⭐ Score mínimo", 0, 99, 0, step=5)
    mods      = ["Todas"] + sorted([m for m in df_raw["modalidade"].dropna().unique() if m])
    mod_sel   = st.selectbox("📋 Modalidade", mods)
    st.markdown("---")
    ultima = df_raw.get("data_importacao", pd.Series(dtype=str)).max()
    st.markdown(f"<div style='font-size:10px;color:rgba(255,255,255,0.4);text-align:center'>Última importação<br>{str(ultima)[:16]}</div>", unsafe_allow_html=True)


# ── Aplicar filtros ───────────────────────────────────────────────────────────
df = df_raw.copy()
if busca:
    mask = (
        df["objeto"].str.lower().str.contains(busca.lower(), na=False) |
        df.get("orgao", pd.Series(dtype=str)).str.lower().str.contains(busca.lower(), na=False)
    )
    df = df[mask]
if uf_sel    != "Todos":  df = df[df["uf"]        == uf_sel]
if fonte_sel != "Todas":  df = df[df["fonte"]      == fonte_sel]
if score_min >  0:        df = df[df["score"]      >= score_min]
if mod_sel   != "Todas":  df = df[df["modalidade"] == mod_sel]


# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_status = st.columns([5, 1])
with col_logo:
    st.markdown(LOGO_SVG, unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:13px;color:{MUTED};margin-top:2px'>Radar de Licitações · Setor de Publicidade</div>", unsafe_allow_html=True)
with col_status:
    st.markdown("<div style='text-align:right;margin-top:8px'><span class='status-ok'><span class='dot-ok'></span>Sheets</span></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("📋 Ver Licitações", use_container_width=True, key="btn_ir_licitacoes"):
        st.switch_page("Pages/Licitacoes.py")

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)


# ── KPIs ──────────────────────────────────────────────────────────────────────
altos       = int((df["score"] >= 70).sum())
medios      = int(((df["score"] >= 50) & (df["score"] < 70)).sum())
valor_total = df["valor_num"].sum()
ufs_n       = df["uf"].nunique()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Editais",       f"{len(df):,}".replace(",", "."), delta=f"de {len(df_raw):,}".replace(",", ".") + " total")
c2.metric("Score Alto ≥70", altos, delta=f"{altos/max(len(df),1)*100:.0f}% filtrado")
c3.metric("Score Médio",   medios)
c4.metric("Valor estimado", f"R$ {valor_total/1e6:.1f}M" if valor_total > 0 else "—")
c5.metric("Estados",       ufs_n)

st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
st.divider()


# ── Gráficos ──────────────────────────────────────────────────────────────────
col_g1, col_g2, col_g3 = st.columns([5, 4, 3])

with col_g1:
    st.markdown("<div class='section-header'>📍 Editais por estado</div>", unsafe_allow_html=True)
    uf_counts = df["uf"].value_counts().head(12).reset_index()
    uf_counts.columns = ["UF", "Qtd"]
    fig_uf = px.bar(uf_counts, x="Qtd", y="UF", orientation="h", color="Qtd",
                    color_continuous_scale=[SURFACE2, AZUL_MID, AZUL], template="plotly_dark")
    fig_uf.update_layout(plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, margin=dict(l=0,r=0,t=4,b=0), height=280,
                         showlegend=False, coloraxis_showscale=False,
                         yaxis=dict(categoryorder="total ascending", tickfont=dict(size=11, color=MUTED), gridcolor=SURFACE2),
                         xaxis=dict(tickfont=dict(size=10, color=MUTED), gridcolor=SURFACE2),
                         font=dict(family="Space Grotesk", color=TEXTO))
    fig_uf.update_traces(marker_line_width=0)
    st.plotly_chart(fig_uf, use_container_width=True)

with col_g2:
    st.markdown("<div class='section-header'>📰 Por fonte</div>", unsafe_allow_html=True)
    fc = df["fonte"].value_counts().reset_index()
    fc.columns = ["Fonte", "Qtd"]
    fig_pie = go.Figure(go.Pie(
        labels=fc["Fonte"], values=fc["Qtd"], hole=0.62,
        marker_colors=[FONTE_CORES.get(f, MUTED) for f in fc["Fonte"]],
        textinfo="label+percent", textfont=dict(size=11, family="Space Grotesk", color=TEXTO),
        insidetextorientation="auto",
    ))
    fig_pie.update_layout(plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, margin=dict(l=0,r=0,t=4,b=0), height=280,
                          showlegend=False, font=dict(family="Space Grotesk", color=TEXTO),
                          annotations=[dict(text=f"<b>{len(df)}</b>", x=0.5, y=0.5, font_size=22, showarrow=False,
                                            font=dict(color=AZUL, family="Space Grotesk"))])
    st.plotly_chart(fig_pie, use_container_width=True)

with col_g3:
    st.markdown("<div class='section-header'>⭐ Por prioridade</div>", unsafe_allow_html=True)
    for label, count in df["prioridade"].value_counts().items():
        pct = count / max(len(df), 1) * 100
        cor = VERDE if "Alto" in label else AMARELO if "Médio" in label else VERMELHO
        st.markdown(
            f"<div style='margin-bottom:14px'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:5px'>"
            f"<span style='font-size:12px;font-weight:500;color:{TEXTO}'>{label}</span>"
            f"<span style='font-size:12px;font-weight:700;color:{cor}'>{count}</span></div>"
            f"<div style='height:7px;background:{SURFACE2};border-radius:4px;overflow:hidden'>"
            f"<div style='height:100%;width:{pct:.0f}%;background:{cor};border-radius:4px'></div></div>"
            f"<div style='font-size:10px;color:{MUTED};margin-top:2px'>{pct:.0f}% do total</div></div>",
            unsafe_allow_html=True,
        )

st.divider()


# ── Top oportunidades + Keywords ──────────────────────────────────────────────
col_top, col_kw = st.columns([3, 2])

with col_top:
    st.markdown("<div class='section-header'>🏆 Top oportunidades</div>", unsafe_allow_html=True)
    for _, r in df.nlargest(10, "score").iterrows():
        sc        = int(r.get("score", 0))
        cor       = score_color(sc)
        vn        = float(r.get("valor_num", 0) or 0)
        valor_str = f"R$ {vn:,.0f}".replace(",", ".") if vn > 0 else "—"
        link      = str(r.get("link", "") or "")
        objeto    = str(r.get("objeto", "") or "")[:130]
        enc       = str(r.get("data_encerramento", "") or "")
        orgao     = str(r.get("orgao", "") or "")[:40]
        link_html = f'<a href="{link}" target="_blank" style="font-size:10px;color:{AZUL};text-decoration:none;font-weight:600">Ver edital →</a>' if link else ""
        enc_html  = f"<span>⏱ {enc}</span>" if enc else ""
        st.markdown(
            f"<div style='background:{SURFACE};border:1px solid {BORDA};border-left:4px solid {cor};border-radius:10px;padding:11px 14px;margin-bottom:8px'>"
            f"<div style='display:flex;justify-content:space-between;align-items:flex-start;gap:8px'>"
            f"<div style='font-size:12.5px;font-weight:500;line-height:1.5;flex:1;color:{TEXTO}'>{objeto}{'...' if len(objeto)==130 else ''}</div>"
            f"<div style='display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0'>"
            f"<span style='background:{cor}18;color:{cor};border:1px solid {cor}30;border-radius:5px;padding:2px 9px;font-size:11px;font-weight:700'>{sc}</span>"
            f"{link_html}</div></div>"
            f"<div style='display:flex;flex-wrap:wrap;gap:10px;margin-top:6px;font-size:11px;color:{MUTED}'>"
            f"<span>📍 {r.get('uf','') or '—'}</span><span>🏛️ {orgao}</span>"
            f"<span>📰 {r.get('fonte','') or '—'}</span><span>💰 {valor_str}</span>{enc_html}</div></div>",
            unsafe_allow_html=True,
        )

with col_kw:
    st.markdown("<div class='section-header'>🏷️ Palavras-chave</div>", unsafe_allow_html=True)
    kw_cnt = Counter()
    for kws in df["palavras_encontradas"].dropna():
        for k in kws.split(","):
            k = k.strip()
            if k: kw_cnt[k] += 1
    kw_top = kw_cnt.most_common(14)
    if kw_top:
        max_cnt = kw_top[0][1]
        for kw, cnt in kw_top:
            pct = cnt / max_cnt * 100
            st.markdown(
                f"<div style='margin-bottom:9px'>"
                f"<div style='display:flex;justify-content:space-between;margin-bottom:3px'>"
                f"<span style='font-size:12px;color:{TEXTO}'>{kw}</span>"
                f"<span style='font-size:11px;color:{MUTED};font-weight:600'>{cnt}</span></div>"
                f"<div style='height:5px;background:{SURFACE2};border-radius:3px;overflow:hidden'>"
                f"<div style='height:100%;width:{pct:.0f}%;background:linear-gradient(90deg,{AZUL_MID},{AZUL});border-radius:3px'></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📅 Publicações recentes</div>", unsafe_allow_html=True)
    if "data_pub" in df.columns:
        por_dia = df.dropna(subset=["data_pub"]).groupby(df["data_pub"].dt.date).size().reset_index(name="n").tail(20)
        por_dia.columns = ["Data", "Editais"]
        fig_line = px.line(por_dia, x="Data", y="Editais", template="plotly_dark", color_discrete_sequence=[AZUL])
        fig_line.update_traces(line_width=2, mode="lines+markers", marker=dict(size=4, color=AZUL))
        fig_line.update_layout(plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, margin=dict(l=0,r=0,t=4,b=0), height=160,
                                xaxis=dict(showgrid=False, tickfont=dict(size=9, color=MUTED), title=None),
                                yaxis=dict(gridcolor=SURFACE2, tickfont=dict(size=9, color=MUTED), title=None),
                                font=dict(family="Space Grotesk", color=TEXTO))
        st.plotly_chart(fig_line, use_container_width=True)

st.divider()
st.markdown(
    f"<div style='font-size:11px;color:{MUTED};text-align:center;padding-bottom:1.5rem'>"
    f"Ampla · {len(df):,} de {len(df_raw):,} editais · Cache 5 min · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    f"</div>".replace(",", "."),
    unsafe_allow_html=True,
)
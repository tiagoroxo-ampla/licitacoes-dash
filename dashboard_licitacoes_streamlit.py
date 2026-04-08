"""
Ampla — Radar de Licitações  v3
================================
Página principal: tabela classificável de licitações.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import traceback
import json
from io import BytesIO
from collections import Counter
from datetime import datetime, date
from pathlib import Path

try:
    import gspread
    GSPREAD_OK = True
except ImportError:
    GSPREAD_OK = False

st.set_page_config(
    page_title="Ampla — Radar de Licitações",
    page_icon="https://www.ampla.com.br/wp-content/uploads/2023/01/cropped-favicon-192x192.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

AZUL     = "#001FFF"
AZUL_MID = "#4d6bff"
BG       = "#0f0f13"
SURFACE  = "#18181e"
SURFACE2 = "#22222c"
BORDA    = "#2e2e3d"
TEXTO    = "#f0f0f8"
MUTED    = "#8888aa"
VERDE    = "#00c48c"
AMARELO  = "#f59e0b"
VERMELHO = "#ef4444"

NOME_PLANILHA    = "Data Licitacoes"
NOME_ABA         = "Página1"
CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SCORE_WEIGHTS = {
    "comunicação digital":       45,
    "publicidade digital":       42,
    "marketing digital":         40,
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
    "veiculação":                  8,
    "relações públicas":           8,
    "anúncio":                     6,
}

LOGO_SVG_BRANCA = '<img src="https://handson.tec.br/static/img/logo/logo-branca.png" height="50">'

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Space Grotesk', sans-serif !important; background-color: {BG} !important; color: {TEXTO}; }}
.stApp {{ background-color: {BG} !important; }}
.block-container {{ background-color: {BG} !important; padding-top: 1.5rem !important; max-width: 1600px; }}
.stApp > header, [data-testid="stHeader"] {{ background: transparent !important; }}
p, span, div, label {{ font-family: 'Space Grotesk', sans-serif !important; }}
h1, h2, h3, h4 {{ font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; color: {TEXTO} !important; }}
[data-baseweb="select"] svg {{ fill: {MUTED} !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] svg {{ fill: white !important; }}
section[data-testid="stSidebar"] {{ background: {AZUL} !important; border-right: none !important; }}
section[data-testid="stSidebar"] * {{ color: rgba(255,255,255,0.9) !important; font-family: 'Space Grotesk', sans-serif !important; }}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stNumberInput label {{
    color: rgba(255,255,255,0.6) !important; font-size: 10px !important;
    text-transform: uppercase !important; letter-spacing: 0.1em !important; font-weight: 600 !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] {{ background: rgba(255,255,255,0.12) !important; border-radius: 8px !important; border: 1px solid rgba(255,255,255,0.22) !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] * {{ color: white !important; background: transparent !important; }}
section[data-testid="stSidebar"] input {{ background: rgba(255,255,255,0.12) !important; border: 1px solid rgba(255,255,255,0.22) !important; border-radius: 8px !important; color: white !important; }}
section[data-testid="stSidebar"] input::placeholder {{ color: rgba(255,255,255,0.35) !important; }}
section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.18) !important; }}
section[data-testid="stSidebar"] .stCheckbox span {{ color: white !important; }}
.stButton > button {{ background: {AZUL} !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; font-family: 'Space Grotesk', sans-serif !important; }}
.stButton > button:hover {{ opacity: 0.82 !important; }}
[data-testid="stDownloadButton"] button {{ background: {SURFACE} !important; color: {AZUL} !important; border: 1.5px solid {AZUL} !important; border-radius: 8px !important; font-weight: 600 !important; }}
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
[data-testid="metric-container"] {{ background: {SURFACE} !important; border: 1px solid {BORDA} !important; border-radius: 14px !important; padding: 1rem 1.2rem !important; border-top: 3px solid {AZUL} !important; }}
[data-testid="stMetricLabel"] {{ font-size: 10px !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; color: {MUTED} !important; font-weight: 600 !important; }}
[data-testid="stMetricValue"] {{ font-weight: 700 !important; font-size: 1.6rem !important; color: {AZUL} !important; }}
[data-testid="stMetricDelta"] {{ font-size: 11px !important; color: {MUTED} !important; }}
[data-testid="stMetricDelta"] svg {{ display: none !important; }}
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

def score_color(s):
    return VERDE if s >= 70 else AMARELO if s >= 50 else VERMELHO

def n_agencias_estimado(v: float) -> str:
    if v <= 0:          return "—"
    if v < 100_000:     return "1–2"
    if v < 500_000:     return "2–5"
    if v < 2_000_000:   return "3–8"
    if v < 10_000_000:  return "5–15"
    return "10+"

def dias_restantes(ts):
    if pd.isna(ts): return None
    try:
        d = ts.date() if hasattr(ts, "date") else ts
        return (d - date.today()).days
    except Exception:
        return None

def excel_bytes(df_: pd.DataFrame) -> bytes:
    cols = ["score", "valor_estimado", "n_agencias", "uf", "municipio",
            "orgao", "objeto", "modalidade", "data_encerramento", "fonte", "link"]
    cols = [c for c in cols if c in df_.columns]
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_[cols].to_excel(w, index=False, sheet_name="Licitações")
        ws = w.sheets["Licitações"]
        for col in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
    return buf.getvalue()


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
    df["valor_num"]  = pd.to_numeric(df.get("valor_estimado", ""), errors="coerce").fillna(0)
    df["n_agencias"] = df["valor_num"].apply(n_agencias_estimado)
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
            raise FileNotFoundError("Credenciais não encontradas.")
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
        if st.button("↻", help="Recarregar"):
            st.cache_data.clear()
            st.rerun()
    st.markdown("---")
    st.markdown("<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.55);margin-bottom:12px'>Filtros</div>", unsafe_allow_html=True)
    filtros_ph = st.empty()


# ── Conectar ──────────────────────────────────────────────────────────────────
sheets_ok = False; sheets_err = None; sheets_tb = None; df_raw = pd.DataFrame()
with st.spinner("Conectando ao Google Sheets..."):
    try:
        gc = conectar_sheets()
        df_raw = carregar_do_sheets(gc, NOME_PLANILHA, NOME_ABA)
        sheets_ok = True
    except Exception as e:
        sheets_err = str(e)
        sheets_tb  = traceback.format_exc()

if not sheets_ok:
    st.error(f"❌ Erro: {sheets_err}")
    st.code(sheets_tb, language="python")
    st.stop()

if df_raw.empty:
    st.warning("Planilha conectada, mas sem dados.")
    st.stop()


# ── Filtros ───────────────────────────────────────────────────────────────────
with filtros_ph.container():
    busca = st.text_input("🔍 Buscar objeto / órgão", placeholder="publicidade...")

    ufs = ["Todos"] + sorted([u for u in df_raw["uf"].dropna().unique() if u])
    uf_sel = st.selectbox("📍 Estado (UF)", ufs)

    fontes = ["Todas"] + sorted([f for f in df_raw["fonte"].dropna().unique() if f])
    fonte_sel = st.selectbox("📰 Fonte", fontes)

    mods = ["Todas"] + sorted([m for m in df_raw["modalidade"].dropna().unique() if m])
    mod_sel = st.selectbox("📋 Modalidade", mods)

    valor_min = st.number_input("💰 Valor mínimo (R$)", min_value=0, value=0, step=50_000)

    apenas_abertos = st.checkbox("🟢 Apenas abertos", value=True)

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
if mod_sel   != "Todas":  df = df[df["modalidade"] == mod_sel]
if valor_min >  0:        df = df[df["valor_num"]  >= valor_min]
if apenas_abertos and "data_enc" in df.columns:
    hoje = pd.Timestamp(date.today())
    df = df[df["data_enc"].isna() | (df["data_enc"] >= hoje)]
df = df.reset_index(drop=True)
total = len(df)


# ── Header ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([5, 2])
with col_h1:
    st.markdown(
        f"<h1 style='margin:0;font-size:1.6rem;letter-spacing:-0.03em;color:{TEXTO}'>"
        f"📋 Radar de Licitações"
        f"<span style='font-size:1rem;font-weight:400;color:{MUTED};margin-left:12px'>"
        f"{total:,} resultado{'s' if total != 1 else ''}</span></h1>".replace(",", "."),
        unsafe_allow_html=True,
    )
    st.markdown(f"<div style='font-size:12px;color:{MUTED};margin-top:2px;margin-bottom:1rem'>Ampla · Setor de Publicidade</div>", unsafe_allow_html=True)
with col_h2:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        if total > 0:
            st.download_button("⬇️ Excel", data=excel_bytes(df),
                file_name=f"licitacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
    with c_dl2:
        st.download_button("⬇️ CSV",
            data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            file_name=f"licitacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv", use_container_width=True)


# ── KPIs ─────────────────────────────────────────────────────────────────────
valor_total = df["valor_num"].sum()
altos = int((df["score"] >= 70).sum())
ufs_n = df["uf"].nunique()
if "data_enc" in df.columns:
    dias_list = [d for d in (dias_restantes(r) for r in df["data_enc"]) if d is not None and d >= 0]
    prazo_med = f"{int(sum(dias_list)/len(dias_list))}d" if dias_list else "—"
else:
    prazo_med = "—"

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Editais",          f"{total:,}".replace(",", "."))
k2.metric("Valor Total",      f"R$ {valor_total/1e6:.1f}M" if valor_total > 0 else "—")
k3.metric("Score Alto ≥70",   altos)
k4.metric("Estados",          ufs_n)
k5.metric("Prazo Médio",      prazo_med)

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
st.divider()


# ── Tabela classificável ──────────────────────────────────────────────────────
if total == 0:
    st.markdown(f"<div style='text-align:center;padding:3rem;color:{MUTED}'>Nenhuma licitação encontrada.</div>", unsafe_allow_html=True)
else:
    # Montar DataFrame de exibição com campos prioritários como colunas
    rows = []
    for _, r in df.iterrows():
        vn  = float(r.get("valor_num", 0) or 0)
        enc = r.get("data_enc", None)
        d   = dias_restantes(enc)

        if d is None:       prazo_label = "—"
        elif d < 0:         prazo_label = "Encerrado"
        elif d == 0:        prazo_label = "Hoje!"
        else:               prazo_label = f"{d}d"

        rows.append({
            "Score":    int(r.get("score", 0)),
            "Valor (R$)": vn,
            "Agências": r.get("n_agencias", "—"),
            "UF":       str(r.get("uf", "") or "—"),
            "Cidade":   str(r.get("municipio", "") or "—"),
            "Órgão":    str(r.get("orgao", "") or "—")[:50],
            "Prazo":    str(r.get("data_encerramento", "") or "")[:16],
            "⏱ Dias":  prazo_label,
            "Fonte":    str(r.get("fonte", "") or ""),
            "Objeto":   str(r.get("objeto", "") or "")[:120],
            "Link":     str(r.get("link", "") or ""),
        })

    df_tabela = pd.DataFrame(rows)

    # Tabela nativa do Streamlit — classificável por qualquer coluna
    st.dataframe(
        df_tabela.drop(columns=["Link"]),
        use_container_width=True,
        height=560,
        column_config={
            "Score": st.column_config.NumberColumn(
                "Score", help="Relevância estimada", format="%d",
                width="small",
            ),
            "Valor (R$)": st.column_config.NumberColumn(
                "Valor (R$)", format="R$ %,.0f", width="medium",
            ),
            "Agências": st.column_config.TextColumn("Agências", width="small"),
            "UF":       st.column_config.TextColumn("UF", width="small"),
            "Cidade":   st.column_config.TextColumn("Cidade", width="medium"),
            "Órgão":    st.column_config.TextColumn("Órgão", width="large"),
            "Prazo":    st.column_config.TextColumn("Prazo", width="medium"),
            "⏱ Dias":  st.column_config.TextColumn("Dias", width="small"),
            "Fonte":    st.column_config.TextColumn("Fonte", width="small"),
            "Objeto":   st.column_config.TextColumn("Objeto (resumo)", width="large"),
        },
        hide_index=True,
    )

    # Links dos editais abaixo da tabela
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-header'>🔗 Editais com link disponível</div>", unsafe_allow_html=True)

    com_link = df_tabela[df_tabela["Link"] != ""].head(30)
    if len(com_link) > 0:
        for _, row in com_link.iterrows():
            sc  = int(row["Score"])
            cor = score_color(sc)
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:12px;padding:8px 14px;"
                f"background:{SURFACE};border:1px solid {BORDA};border-left:3px solid {cor};"
                f"border-radius:8px;margin-bottom:6px'>"
                f"<span style='background:{cor}18;color:{cor};border:1px solid {cor}40;"
                f"border-radius:5px;padding:2px 8px;font-size:11px;font-weight:700;flex-shrink:0'>{sc}</span>"
                f"<span style='font-size:11px;color:{MUTED};flex-shrink:0'>{row['UF']} · {row['Valor (R$)'] and 'R$ {:,.0f}'.format(row['Valor (R$)']).replace(',','.') or '—'} · {row['⏱ Dias']}</span>"
                f"<span style='font-size:12px;color:{TEXTO};flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{row['Objeto']}</span>"
                f"<a href='{row['Link']}' target='_blank' style='background:{AZUL};color:white;"
                f"border-radius:6px;padding:4px 12px;font-size:11px;font-weight:600;"
                f"text-decoration:none;flex-shrink:0'>Ver edital →</a>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(f"<div style='color:{MUTED};font-size:12px'>Nenhum edital com link disponível nos resultados atuais.</div>", unsafe_allow_html=True)

st.divider()
st.markdown(
    f"<div style='font-size:11px;color:{MUTED};text-align:center;padding-bottom:1.5rem'>"
    f"Ampla · {total:,} de {len(df_raw):,} editais · Cache 5 min · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    f"</div>".replace(",", "."),
    unsafe_allow_html=True,
)
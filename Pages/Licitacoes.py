"""
Ampla — Radar de Licitações  v3
================================
Página: /Licitações — lista detalhada de editais.
Destaque: valor · local · órgão · agências · prazo.
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_OK = True
except ImportError:
    GSPREAD_OK = False

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ampla — Licitações",
    page_icon="https://www.ampla.com.br/wp-content/uploads/2023/01/cropped-favicon-192x192.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta ────────────────────────────────────────────────────────────────────
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
CREDENTIALS_PATH = Path(__file__).parent.parent / "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

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

LOGO_SVG_BRANCA = '<img src="https://handson.tec.br/static/img/logo/logo-branca.png" height="50">'

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Space Grotesk', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXTO};
}}
.stApp {{ background-color: {BG} !important; }}
.block-container {{
    background-color: {BG} !important;
    padding-top: 1.5rem !important;
    max-width: 1400px;
}}
.stApp > header, [data-testid="stHeader"] {{ background: transparent !important; }}
p, span, div, label {{ font-family: 'Space Grotesk', sans-serif !important; }}
h1, h2, h3, h4 {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    color: {TEXTO} !important;
}}

/* Sidebar */
[data-baseweb="select"] svg {{ fill: {MUTED} !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] svg {{ fill: white !important; }}
section[data-testid="stSidebar"] {{
    background: {AZUL} !important;
    border-right: none !important;
}}
section[data-testid="stSidebar"] * {{
    color: rgba(255,255,255,0.9) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stMultiSelect label {{
    color: rgba(255,255,255,0.6) !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    font-weight: 600 !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] {{
    background: rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] * {{
    color: white !important;
    background: transparent !important;
}}
section[data-testid="stSidebar"] input {{
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    border-radius: 8px !important;
    color: white !important;
}}
section[data-testid="stSidebar"] input::placeholder {{ color: rgba(255,255,255,0.35) !important; }}
section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.18) !important; }}
section[data-testid="stSidebar"] .stCheckbox span {{ color: white !important; }}

/* Botões */
.stButton > button {{
    background: {AZUL} !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}
.stButton > button:hover {{ opacity: 0.82 !important; }}
[data-testid="stDownloadButton"] button {{
    background: {SURFACE} !important;
    color: {AZUL} !important;
    border: 1.5px solid {AZUL} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
[data-testid="stDownloadButton"] button:hover {{ background: rgba(0,31,255,0.1) !important; }}

/* Inputs */
[data-baseweb="select"] {{ background: {SURFACE2} !important; border-radius: 8px !important; border: 1px solid {BORDA} !important; }}
[data-baseweb="popover"] ul {{ background: {SURFACE2} !important; }}
[data-baseweb="popover"] li {{ background: {SURFACE2} !important; color: {TEXTO} !important; }}
[data-baseweb="popover"] li:hover {{ background: {BORDA} !important; }}
.stTextInput input {{
    background: {SURFACE2} !important;
    border: 1px solid {BORDA} !important;
    border-radius: 8px !important;
    color: {TEXTO} !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDA}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {MUTED}; }}
hr {{ border-color: {BORDA} !important; }}

.section-header {{
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: {MUTED} !important;
    margin-bottom: 0.75rem !important;
}}

/* Cards */
.lic-card {{
    background: {SURFACE};
    border: 1px solid {BORDA};
    border-radius: 14px;
    margin-bottom: 14px;
    overflow: hidden;
}}
.lic-card:hover {{ border-color: {AZUL_MID}; }}
.lic-card-top {{
    padding: 14px 18px 10px 18px;
    border-bottom: 1px solid {BORDA};
}}
.lic-card-body {{
    display: grid;
    grid-template-columns: 2fr 2fr 1.5fr 1fr 1.5fr;
}}
.lic-field {{
    padding: 12px 18px;
    border-right: 1px solid {BORDA};
}}
.lic-field:last-child {{ border-right: none; }}
.lic-field-label {{
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: {MUTED};
    margin-bottom: 4px;
}}
.lic-field-value {{
    font-size: 13px;
    font-weight: 600;
    color: {TEXTO};
    line-height: 1.35;
}}
.lic-tag {{
    display: inline-block;
    background: rgba(77,107,255,0.12);
    color: {AZUL_MID};
    border: 1px solid rgba(77,107,255,0.22);
    border-radius: 20px;
    padding: 2px 9px;
    font-size: 10px;
    font-weight: 600;
    margin-right: 4px;
    margin-bottom: 2px;
}}

/* Faixa de resumo */
.resumo-strip {{
    display: flex;
    gap: 20px;
    align-items: center;
    background: {SURFACE};
    border: 1px solid {BORDA};
    border-radius: 12px;
    padding: 12px 20px;
    margin-bottom: 18px;
    flex-wrap: wrap;
}}
.resumo-item {{ display: flex; flex-direction: column; gap: 2px; }}
.resumo-label {{
    font-size: 9px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em; color: {MUTED};
}}
.resumo-value {{ font-size: 16px; font-weight: 700; color: {AZUL}; }}
.resumo-sep {{ width: 1px; height: 36px; background: {BORDA}; }}

/* Corrige ícone nativo de recolher sidebar (Material Icons não carregado) */
[data-testid="collapsedControl"] span,
button[data-testid="baseButton-headerNoPadding"] span,
[data-testid="stSidebarCollapsedControl"] span {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0 !important;
}}
[data-testid="collapsedControl"] span::after,
button[data-testid="baseButton-headerNoPadding"] span::after,
[data-testid="stSidebarCollapsedControl"] span::after {{
    content: '☰' !important;
    font-size: 18px !important;
    color: {TEXTO} !important;
}}
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


def score_label(s: int) -> str:
    if s >= 70: return "🟢 Alto"
    if s >= 50: return "🟡 Médio"
    return "🔴 Baixo"


def score_color(s: int) -> str:
    if s >= 70: return VERDE
    if s >= 50: return AMARELO
    return VERMELHO


def dias_restantes(ts) -> int | None:
    if pd.isna(ts):
        return None
    try:
        d = ts.date() if hasattr(ts, "date") else ts
        return (d - date.today()).days
    except Exception:
        return None


def prazo_html(ts) -> str:
    dias = dias_restantes(ts)
    if dias is None:
        return f"<span style='color:{MUTED}'>—</span>"
    if dias < 0:
        return f"<span style='color:{VERMELHO};font-weight:700'>Encerrado</span>"
    if dias == 0:
        return f"<span style='color:{VERMELHO};font-weight:700'>Hoje!</span>"
    if dias <= 5:
        return f"<span style='color:{VERMELHO};font-weight:700'>⚠ {dias}d</span>"
    if dias <= 15:
        return f"<span style='color:{AMARELO};font-weight:700'>⏳ {dias}d</span>"
    return f"<span style='color:{VERDE};font-weight:700'>✓ {dias}d</span>"


def n_agencias_estimado(valor_num: float) -> str:
    if valor_num <= 0:   return "—"
    if valor_num < 100_000:   return "1–2"
    if valor_num < 500_000:   return "2–5"
    if valor_num < 2_000_000: return "3–8"
    if valor_num < 10_000_000: return "5–15"
    return "10+"


def df_para_excel(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Licitações")
        ws = w.sheets["Licitações"]
        for col in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
    return buf.getvalue()


def excel_bytes(df_: pd.DataFrame) -> bytes:
    cols = ["score", "prioridade", "valor_estimado", "uf", "municipio", "orgao",
            "objeto", "modalidade", "data_publicacao", "data_encerramento", "fonte", "link"]
    cols = [c for c in cols if c in df_.columns]
    return df_para_excel(df_[cols])


# ── Google Sheets ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def carregar_do_sheets(_gc, planilha_nome: str, aba_nome: str) -> pd.DataFrame:
    planilha = _gc.open(planilha_nome)
    ws = planilha.worksheet(aba_nome)
    dados = ws.get_all_records(default_blank="")
    if not dados:
        return pd.DataFrame()
    df = pd.DataFrame(dados).fillna("")
    df["score"]     = df.apply(calcular_score, axis=1)
    df["prioridade"] = df["score"].apply(score_label)
    df["valor_num"] = pd.to_numeric(df.get("valor_estimado", ""), errors="coerce").fillna(0)
    if "data_publicacao"   in df.columns:
        df["data_pub"] = pd.to_datetime(df["data_publicacao"],   errors="coerce")
    if "data_encerramento" in df.columns:
        df["data_enc"] = pd.to_datetime(df["data_encerramento"], errors="coerce")
    return df.sort_values("score", ascending=False).reset_index(drop=True)


def conectar_sheets():
    if "gc" not in st.session_state:
        if not GSPREAD_OK:
            st.error("Instale: pip install gspread google-auth")
            st.stop()
        if not CREDENTIALS_PATH.exists():
            st.error(f"credentials.json não encontrado em: {CREDENTIALS_PATH}")
            st.stop()
        creds = Credentials.from_service_account_file(str(CREDENTIALS_PATH), scopes=SCOPES)
        st.session_state["gc"] = gspread.authorize(creds)
    return st.session_state["gc"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(LOGO_SVG_BRANCA, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(
        "<div style='font-size:10px;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.1em;color:rgba(255,255,255,0.55);margin-bottom:8px'>"
        "Dados</div>",
        unsafe_allow_html=True,
    )
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        st.markdown(
            f"<div style='font-size:12px;color:rgba(255,255,255,0.85)'>"
            f"📊 {NOME_PLANILHA}</div>",
            unsafe_allow_html=True,
        )
    with col_s2:
        if st.button("↻", help="Recarregar"):
            st.cache_data.clear()
            st.rerun()

    # Botão voltar ao dashboard
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    if st.button("← Voltar ao Dashboard", use_container_width=True, key="btn_voltar"):
        st.switch_page("dashboard_licitacoes_streamlit.py")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:10px;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.1em;color:rgba(255,255,255,0.55);margin-bottom:12px'>"
        "Filtros</div>",
        unsafe_allow_html=True,
    )
    filtros_ph = st.empty()


# ── Conectar e carregar ───────────────────────────────────────────────────────
with st.spinner("Conectando..."):
    try:
        gc     = conectar_sheets()
        df_raw = carregar_do_sheets(gc, NOME_PLANILHA, NOME_ABA)
        ok     = True
        err    = None
    except Exception as e:
        ok  = False
        err = str(e)
        df_raw = pd.DataFrame()

if not ok:
    st.error(f"Erro ao conectar ao Google Sheets: {err}")
    st.stop()
if df_raw.empty:
    st.warning("Planilha conectada, mas sem dados.")
    st.stop()


# ── Filtros sidebar ───────────────────────────────────────────────────────────
with filtros_ph.container():
    busca = st.text_input("🔍 Buscar objeto / órgão", placeholder="publicidade...")

    ufs = ["Todos"] + sorted([u for u in df_raw["uf"].dropna().unique() if u])
    uf_sel = st.selectbox("📍 Estado (UF)", ufs)

    score_min = st.slider("⭐ Score mínimo", 0, 99, 0, step=5)

    fontes = ["Todas"] + sorted([f for f in df_raw["fonte"].dropna().unique() if f])
    fonte_sel = st.selectbox("📰 Fonte", fontes)

    mods = ["Todas"] + sorted([m for m in df_raw["modalidade"].dropna().unique() if m])
    mod_sel = st.selectbox("📋 Modalidade", mods)

    valor_min = st.number_input("💰 Valor mínimo (R$)", min_value=0, value=0, step=10000)

    apenas_abertos = st.checkbox("🟢 Apenas abertos", value=True)

    ordem_opcoes = {
        "Score (maior primeiro)":    ("score",    False),
        "Prazo (mais urgente)":      ("data_enc", True),
        "Valor (maior primeiro)":    ("valor_num", False),
        "Publicação (mais recente)": ("data_pub",  False),
    }
    ordem_sel = st.selectbox("↕️ Ordenar por", list(ordem_opcoes.keys()))

    POR_PAG = st.select_slider("Resultados por página", options=[5, 10, 20, 50], value=10)

    st.markdown("---")
    ultima = df_raw.get("data_importacao", pd.Series(dtype=str)).max()
    st.markdown(
        f"<div style='font-size:10px;color:rgba(255,255,255,0.4);text-align:center'>"
        f"Última importação<br>{str(ultima)[:16]}</div>",
        unsafe_allow_html=True,
    )


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
if valor_min >  0:        df = df[df["valor_num"]  >= valor_min]

if apenas_abertos and "data_enc" in df.columns:
    hoje = pd.Timestamp(date.today())
    df = df[df["data_enc"].isna() | (df["data_enc"] >= hoje)]

ord_col, ord_asc = ordem_opcoes[ordem_sel]
if ord_col in df.columns:
    df = df.sort_values(ord_col, ascending=ord_asc, na_position="last")

df = df.reset_index(drop=True)

# ── Paginação ─────────────────────────────────────────────────────────────────
total  = len(df)
n_pags = max(1, -(-total // POR_PAG))

if "pag_licitacoes" not in st.session_state:
    st.session_state["pag_licitacoes"] = 1

pag    = max(1, min(st.session_state["pag_licitacoes"], n_pags))
inicio = (pag - 1) * POR_PAG
fim    = min(inicio + POR_PAG, total)
df_pag = df.iloc[inicio:fim]


# ── Header ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    st.markdown(
        f"<h1 style='margin:0;font-size:1.6rem;letter-spacing:-0.03em;color:{TEXTO}'>"
        f"📋 Licitações"
        f"<span style='font-size:1rem;font-weight:400;color:{MUTED};margin-left:12px'>"
        f"{total:,} resultado{'s' if total != 1 else ''}</span></h1>".replace(",", "."),
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:12px;color:{MUTED};margin-top:2px;margin-bottom:1rem'>"
        f"Ampla · Radar de Licitações · Setor de Publicidade</div>",
        unsafe_allow_html=True,
    )
with col_h2:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if total > 0:
        st.download_button(
            "⬇️ Excel",
            data=excel_bytes(df),
            file_name=f"licitacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ── Faixa de resumo ───────────────────────────────────────────────────────────
valor_total = df["valor_num"].sum()
altos       = int((df["score"] >= 70).sum())
ufs_n       = df["uf"].nunique()

if "data_enc" in df.columns:
    dias_list = [d for d in (dias_restantes(r) for r in df["data_enc"])
                 if d is not None and d >= 0]
    prazo_med = f"{int(sum(dias_list)/len(dias_list))}d" if dias_list else "—"
else:
    prazo_med = "—"

st.markdown(
    f"""
    <div class="resumo-strip">
      <div class="resumo-item">
        <div class="resumo-label">Valor total estimado</div>
        <div class="resumo-value">{"R$ " + f"{valor_total/1e6:.1f}M" if valor_total > 0 else "—"}</div>
      </div>
      <div class="resumo-sep"></div>
      <div class="resumo-item">
        <div class="resumo-label">Score alto ≥70</div>
        <div class="resumo-value">{altos}</div>
      </div>
      <div class="resumo-sep"></div>
      <div class="resumo-item">
        <div class="resumo-label">Estados</div>
        <div class="resumo-value">{ufs_n}</div>
      </div>
      <div class="resumo-sep"></div>
      <div class="resumo-item">
        <div class="resumo-label">Prazo médio restante</div>
        <div class="resumo-value">{prazo_med}</div>
      </div>
      <div class="resumo-sep"></div>
      <div class="resumo-item">
        <div class="resumo-label">Mostrando</div>
        <div class="resumo-value">{inicio+1 if total > 0 else 0}–{fim} de {total}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Cabeçalho das colunas ─────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='display:grid;grid-template-columns:2fr 2fr 1.5fr 1fr 1.5fr;
                padding:6px 18px;border-radius:8px 8px 0 0;
                background:{SURFACE2};border:1px solid {BORDA};border-bottom:none'>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:{AZUL}'>💰 Valor</div>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:{AZUL}'>📍 Local</div>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:{AZUL}'>🏛️ Órgão Contratante</div>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:{AZUL}'>🏢 Agências</div>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:{AZUL}'>⏱ Prazo</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Cards ─────────────────────────────────────────────────────────────────────
if total == 0:
    st.markdown(
        f"<div style='text-align:center;padding:3rem;color:{MUTED}'>"
        f"Nenhuma licitação encontrada com os filtros selecionados.</div>",
        unsafe_allow_html=True,
    )
else:
    for _, r in df_pag.iterrows():
        sc      = int(r.get("score", 0))
        cor     = score_color(sc)
        vn      = float(r.get("valor_num", 0) or 0)
        objeto  = str(r.get("objeto",  "") or "")
        orgao   = str(r.get("orgao",   "") or "")
        uf      = str(r.get("uf",      "") or "—")
        mun     = str(r.get("municipio","") or "")
        fonte   = str(r.get("fonte",   "") or "")
        mod     = str(r.get("modalidade","") or "")
        link    = str(r.get("link",    "") or "")
        pub     = str(r.get("data_publicacao","") or "")[:10]
        enc     = r.get("data_enc", None)
        enc_str = str(r.get("data_encerramento","") or "")[:10]
        kws     = str(r.get("palavras_encontradas","") or "")

        valor_disp = f"R$ {vn:,.0f}".replace(",", ".") if vn > 0 else "A definir"
        local_sec  = mun if mun and mun.lower() != uf.lower() else ""

        tags_html = "".join(
            f"<span class='lic-tag'>{t.strip()}</span>"
            for t in kws.split(",") if t.strip()
        )[:3*80]  # limita ao HTML dos primeiros 3 tags aproximadamente

        tags_list = [t.strip() for t in kws.split(",") if t.strip()][:3]
        tags_html = "".join(f"<span class='lic-tag'>{t}</span>" for t in tags_list)

        link_html = (
            f'<a href="{link}" target="_blank" style="'
            f'display:inline-block;background:{AZUL};color:white;border-radius:6px;'
            f'padding:4px 12px;font-size:11px;font-weight:600;text-decoration:none">'
            f'Ver edital →</a>'
        ) if link else ""

        score_badge = (
            f"<span style='background:{cor}18;color:{cor};border:1px solid {cor}40;"
            f"border-radius:6px;padding:3px 10px;font-size:12px;font-weight:700;"
            f"margin-right:8px'>{sc}</span>"
        )

        obj_curto = objeto[:160] + ("..." if len(objeto) > 160 else "")
        orgao_curto = orgao[:60] + ("..." if len(orgao) > 60 else "")

        st.markdown(
            f"""
            <div class="lic-card" style="border-left:4px solid {cor}">
              <div class="lic-card-top">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">
                  <div style="flex:1">
                    {score_badge}
                    <span style="font-size:9px;background:{SURFACE2};color:{MUTED};
                                 border:1px solid {BORDA};border-radius:4px;
                                 padding:2px 7px;font-weight:600;margin-right:6px">{mod}</span>
                    <span style="font-size:9px;background:{SURFACE2};color:{MUTED};
                                 border:1px solid {BORDA};border-radius:4px;
                                 padding:2px 7px;font-weight:600">{fonte}</span>
                    <div style="margin-top:8px;font-size:13px;font-weight:500;
                                color:{TEXTO};line-height:1.5">{obj_curto}</div>
                    <div style="margin-top:6px">{tags_html}</div>
                  </div>
                  <div style="flex-shrink:0;text-align:right;min-width:110px">
                    {link_html}
                    <div style="font-size:10px;color:{MUTED};margin-top:8px">Pub. {pub}</div>
                  </div>
                </div>
              </div>
              <div class="lic-card-body">
                <div class="lic-field">
                  <div class="lic-field-label">💰 Valor estimado</div>
                  <div class="lic-field-value" style="font-size:15px;color:{VERDE};font-weight:700">{valor_disp}</div>
                </div>
                <div class="lic-field">
                  <div class="lic-field-label">📍 Local</div>
                  <div class="lic-field-value">
                    <span style="font-size:15px;font-weight:700">{uf}</span>
                    {'<br><span style="font-size:11px;color:' + MUTED + '">' + local_sec + '</span>' if local_sec else ''}
                  </div>
                </div>
                <div class="lic-field">
                  <div class="lic-field-label">🏛️ Órgão contratante</div>
                  <div class="lic-field-value" style="font-size:12px">{orgao_curto}</div>
                </div>
                <div class="lic-field">
                  <div class="lic-field-label">🏢 Agências</div>
                  <div class="lic-field-value" style="font-size:15px;color:{AZUL_MID}">{n_agencias_estimado(vn)}</div>
                </div>
                <div class="lic-field">
                  <div class="lic-field-label">⏱ Prazo</div>
                  <div class="lic-field-value">
                    {prazo_html(enc)}
                    <div style="font-size:11px;color:{MUTED};margin-top:3px">{enc_str}</div>
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Paginação ─────────────────────────────────────────────────────────────────
if n_pags > 1:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    col_prev, col_info, col_next = st.columns([1, 4, 1])

    with col_prev:
        if st.button("← Anterior", disabled=(pag <= 1), use_container_width=True):
            st.session_state["pag_licitacoes"] = pag - 1
            st.rerun()
    with col_info:
        st.markdown(
            f"<div style='text-align:center;font-size:12px;color:{MUTED};padding-top:8px'>"
            f"Página {pag} de {n_pags} · {total} resultados</div>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Próxima →", disabled=(pag >= n_pags), use_container_width=True):
            st.session_state["pag_licitacoes"] = pag + 1
            st.rerun()


# ── Exportar rodapé ───────────────────────────────────────────────────────────
st.divider()
ce1, ce2, ce3 = st.columns([2, 2, 4])
with ce1:
    st.download_button(
        "⬇️ Exportar CSV",
        data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name=f"licitacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
with ce2:
    if total > 0:
        st.download_button(
            "📊 Exportar Excel",
            data=excel_bytes(df),
            file_name=f"licitacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
with ce3:
    st.markdown(
        f"<div style='font-size:11px;color:{MUTED};padding-top:10px'>"
        f"Ampla · {total:,} de {len(df_raw):,} editais · "
        f"Cache 5 min · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        f"</div>".replace(",", "."),
        unsafe_allow_html=True,
    )
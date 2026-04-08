"""
Ampla — Radar de Licitações  v3
================================
Página: /Licitações — tabela principal com filtros avançados.
Foco: Valor, Agências, Local, Órgão, Prazo — dados CLASSIFICÁVEIS.
Download de PDF dos editais.
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date, timedelta
from pathlib import Path
import requests

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
    max-width: 1600px;
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

/* Tabela customizada */
[data-testid="dataframe"] {{
    width: 100% !important;
    border-radius: 10px;
    overflow: hidden;
}}
[data-testid="dataframe"] th {{
    background-color: {SURFACE2} !important;
    color: {AZUL} !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    border: none !important;
    padding: 12px 8px !important;
}}
[data-testid="dataframe"] td {{
    border: none !important;
    padding: 10px 8px !important;
    color: {TEXTO} !important;
    background-color: {SURFACE} !important;
    font-size: 12px !important;
}}
[data-testid="dataframe"] tr:hover {{
    background-color: {SURFACE2} !important;
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


def score_color(s: int) -> str:
    if s >= 70: return VERDE
    if s >= 50: return AMARELO
    return VERMELHO


def categorizar_licitacao(row) -> str:
    """Categoriza em COMUNICAÇÃO DIGITAL ou PUBLICIDADE E PROPAGANDA"""
    texto = f"{row.get('objeto','') or ''} {row.get('palavras_encontradas','') or ''}".lower()

    digital_kws = ["comunicação digital", "publicidade digital", "marketing digital",
                   "redes sociais", "mídia social", "social media", "seo", "sem",
                   "email marketing", "automação digital"]
    pub_kws = ["publicidade", "propaganda", "campanha publicitária", "agência de publicidade",
               "criação publicitária", "mídia exterior", "outdoor", "busdoor"]

    digital_score = sum(1 for kw in digital_kws if kw in texto)
    pub_score = sum(1 for kw in pub_kws if kw in texto)

    if digital_score > pub_score:
        return "Comunicação Digital"
    elif pub_score > 0:
        return "Publicidade e Propaganda"
    return "Geral"


def dias_restantes(ts) -> int | None:
    if pd.isna(ts):
        return None
    try:
        d = ts.date() if hasattr(ts, "date") else ts
        return (d - date.today()).days
    except Exception:
        return None


def n_agencias_estimado(valor_num: float) -> str:
    if valor_num <= 0:        return "—"
    if valor_num < 100_000:   return "1–2"
    if valor_num < 500_000:   return "2–5"
    if valor_num < 2_000_000: return "3–8"
    if valor_num < 10_000_000: return "5–15"
    return "10+"


def baixar_pdf_edital(url: str, nome_arquivo: str) -> bytes:
    """Baixa PDF do edital da URL e retorna como bytes"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception:
        pass
    return None


def excel_bytes(df_: pd.DataFrame) -> bytes:
    """Exporta dados para Excel"""
    cols = ["categoria", "score", "valor_estimado", "uf", "municipio", "orgao",
            "objeto", "data_encerramento", "fonte", "n_agencias"]
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
def carregar_do_sheets(_gc, planilha_nome: str, aba_nome: str) -> pd.DataFrame:
    planilha = _gc.open(planilha_nome)
    ws = planilha.worksheet(aba_nome)
    dados = ws.get_all_records(default_blank="")
    if not dados:
        return pd.DataFrame()
    df = pd.DataFrame(dados).fillna("")
    df["score"]      = df.apply(calcular_score, axis=1)
    df["categoria"]  = df.apply(categorizar_licitacao, axis=1)
    df["valor_num"]  = pd.to_numeric(df.get("valor_estimado", ""), errors="coerce").fillna(0)
    df["n_agencias"] = df["valor_num"].apply(n_agencias_estimado)
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

        if "credentials" in st.secrets:
            raw = dict(st.secrets["credentials"])
            raw["private_key"] = raw["private_key"].replace("\\n", "\n")
        else:
            local_path = Path(__file__).parent.parent / "credentials.json"
            if not local_path.exists():
                st.error("credentials.json não encontrado e Secrets não configurados.")
                st.stop()
            import json
            with open(local_path) as f:
                raw = json.load(f)

        gc = gspread.service_account_from_dict(raw)
        st.session_state["gc"] = gc

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
    st.error(f"Erro: {err}")
    if "credentials" in st.secrets:
        raw = dict(st.secrets["credentials"])
        pk  = raw.get("private_key", "NÃO ENCONTRADO")
        st.write("**private_key (início):**", repr(pk[:80]))
        st.write("**client_email:**", raw.get("client_email", "NÃO ENCONTRADO"))
    else:
        st.warning("Chave `[credentials]` NÃO encontrada nos Secrets!")
    st.stop()
if df_raw.empty:
    st.warning("Planilha conectada, mas sem dados.")
    st.stop()


# ── Filtros sidebar ───────────────────────────────────────────────────────────
with filtros_ph.container():
    busca = st.text_input("🔍 Buscar objeto / órgão", placeholder="publicidade...")

    ufs = ["Todos"] + sorted([u for u in df_raw["uf"].dropna().unique() if u])
    uf_sel = st.selectbox("📍 Estado (UF)", ufs)

    valor_min = st.number_input("💰 Valor mínimo (R$)", min_value=0, value=0, step=50000)
    valor_max = st.number_input("💰 Valor máximo (R$)", min_value=0, value=100000000, step=50000)

    categorias = ["Todas"] + sorted([c for c in df_raw["categoria"].dropna().unique() if c])
    categoria_sel = st.selectbox("📌 Categoria", categorias)

    fontes = ["Todas"] + sorted([f for f in df_raw["fonte"].dropna().unique() if f])
    fonte_sel = st.selectbox("📰 Fonte", fontes)

    apenas_abertos = st.checkbox("🟢 Apenas abertos", value=True)

    ordem_opcoes = {
        "Valor (maior primeiro)":    ("valor_num", False),
        "Prazo (mais urgente)":      ("data_enc", True),
        "Score (maior primeiro)":    ("score", False),
        "Publicação (mais recente)": ("data_pub", False),
    }
    ordem_sel = st.selectbox("↕️ Ordenar por", list(ordem_opcoes.keys()))

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

if uf_sel    != "Todos":        df = df[df["uf"]        == uf_sel]
if categoria_sel != "Todas":    df = df[df["categoria"] == categoria_sel]
if fonte_sel != "Todas":        df = df[df["fonte"]      == fonte_sel]
if valor_min >  0:              df = df[df["valor_num"]  >= valor_min]
if valor_max > 0:               df = df[df["valor_num"]  <= valor_max]

if apenas_abertos and "data_enc" in df.columns:
    hoje = pd.Timestamp(date.today())
    df = df[df["data_enc"].isna() | (df["data_enc"] >= hoje)]

ord_col, ord_asc = ordem_opcoes[ordem_sel]
if ord_col in df.columns:
    df = df.sort_values(ord_col, ascending=ord_asc, na_position="last")

df = df.reset_index(drop=True)


# ── Header ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    st.markdown(
        f"<h1 style='margin:0;font-size:1.6rem;letter-spacing:-0.03em;color:{TEXTO}'>"
        f"📋 Licitações"
        f"<span style='font-size:1rem;font-weight:400;color:{MUTED};margin-left:12px'>"
        f"{len(df):,} resultado{'s' if len(df) != 1 else ''}</span></h1>".replace(",", "."),
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:12px;color:{MUTED};margin-top:2px;margin-bottom:1rem'>"
        f"Tabela de licitações filtrada e classificável por valor, estado, órgão, e data de entrega</div>",
        unsafe_allow_html=True,
    )
with col_h2:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if len(df) > 0:
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
    <div style='display:flex;gap:20px;align-items:center;background:{SURFACE};border:1px solid {BORDA};
                border-radius:12px;padding:12px 20px;margin-bottom:18px;flex-wrap:wrap'>
      <div style='display:flex;flex-direction:column;gap:2px'>
        <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{MUTED}'>Valor Total</div>
        <div style='font-size:16px;font-weight:700;color:{AZUL}'>{"R$ " + f"{valor_total/1e6:.1f}M" if valor_total > 0 else "—"}</div>
      </div>
      <div style='width:1px;height:36px;background:{BORDA}'></div>
      <div style='display:flex;flex-direction:column;gap:2px'>
        <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{MUTED}'>Score Alto ≥70</div>
        <div style='font-size:16px;font-weight:700;color:{VERDE}'>{altos}</div>
      </div>
      <div style='width:1px;height:36px;background:{BORDA}'></div>
      <div style='display:flex;flex-direction:column;gap:2px'>
        <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{MUTED}'>Estados</div>
        <div style='font-size:16px;font-weight:700;color:{AZUL}>{ufs_n}</div>
      </div>
      <div style='width:1px;height:36px;background:{BORDA}'></div>
      <div style='display:flex;flex-direction:column;gap:2px'>
        <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{MUTED}'>Prazo Médio</div>
        <div style='font-size:16px;font-weight:700;color:{AMARELO}'>{prazo_med}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Tabela Principal ──────────────────────────────────────────────────────────
if len(df) == 0:
    st.markdown(
        f"<div style='text-align:center;padding:3rem;color:{MUTED}'>"
        f"Nenhuma licitação encontrada com os filtros selecionados.</div>",
        unsafe_allow_html=True,
    )
else:
    # Preparar dados para exibição
    df_display = df[[
        "categoria", "valor_num", "uf", "municipio", "orgao",
        "objeto", "data_encerramento", "n_agencias", "fonte", "score", "link"
    ]].copy()

    df_display.columns = [
        "Categoria", "Valor (R$)", "UF", "Município", "Órgão",
        "Objeto", "Prazo", "Agências", "Fonte", "Score", "Link"
    ]

    # Formatar colunas
    df_display["Valor (R$)"] = df_display["Valor (R$)"].apply(
        lambda x: f"R$ {x:,.0f}".replace(",", ".") if x > 0 else "A definir"
    )
    df_display["Prazo"] = df_display["Prazo"].apply(
        lambda x: str(x)[:10] if pd.notna(x) else "—"
    )

    # Exibir tabela
    st.dataframe(
        df_display.drop("Link", axis=1),
        use_container_width=True,
        height=600,
    )

    # Seção de download de PDFs
    st.divider()
    st.markdown(f"<div class='section-header'>📥 Baixar Editais em PDF</div>", unsafe_allow_html=True)

    col_info, col_acao = st.columns([4, 1])
    with col_info:
        st.markdown(
            f"<div style='font-size:12px;color:{MUTED}'>Selecione o edital abaixo para baixar o PDF completo:</div>",
            unsafe_allow_html=True
        )

    # Criar lista de editais para download
    editais_disponiveis = df[df["link"].notna() & (df["link"] != "")].copy()

    if len(editais_disponiveis) > 0:
        for idx, (_, row) in enumerate(editais_disponiveis.head(20).iterrows()):
            objeto_short = str(row.get("objeto", ""))[:80]
            uf = row.get("uf", "—")
            valor = row.get("valor_num", 0)
            valor_str = f"R$ {valor:,.0f}".replace(",", ".") if valor > 0 else "A definir"
            link = row.get("link", "")

            col_desc, col_btn = st.columns([5, 1])
            with col_desc:
                st.markdown(
                    f"<div style='font-size:12px;color:{TEXTO};font-weight:500'>{objeto_short}...</div>"
                    f"<div style='font-size:11px;color:{MUTED};margin-top:2px'>{uf} · {valor_str}</div>",
                    unsafe_allow_html=True
                )
            with col_btn:
                if st.button("📥", key=f"pdf_btn_{idx}", help="Baixar PDF"):
                    pdf_data = baixar_pdf_edital(link, f"edital_{idx}.pdf")
                    if pdf_data:
                        st.download_button(
                            "⬇️ PDF",
                            data=pdf_data,
                            file_name=f"edital_{uf}_{idx}.pdf",
                            mime="application/pdf",
                            key=f"pdf_dl_{idx}"
                        )
                    else:
                        st.warning("Não foi possível baixar o PDF")
    else:
        st.info("Nenhum edital com link disponível para download.")


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
    if len(df) > 0:
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
        f"Ampla · {len(df):,} de {len(df_raw):,} editais · "
        f"Cache 5 min · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        f"</div>".replace(",", "."),
        unsafe_allow_html=True,
    )
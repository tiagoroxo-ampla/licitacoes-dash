"""
Ampla — Radar de Licitações  v3
"""

import streamlit as st
import pandas as pd
import traceback
import json
from io import BytesIO
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
    initial_sidebar_state="collapsed",
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
    "comunicação digital": 45, "publicidade digital": 42, "marketing digital": 40,
    "agência de publicidade": 40, "campanha publicitária": 35, "criação publicitária": 35,
    "veiculação de mídia": 30, "produção audiovisual": 28, "comunicação social": 25,
    "assessoria de comunicação": 25, "serviços de comunicação": 22, "publicidade": 20,
    "propaganda": 18, "mídia exterior": 18, "inserção televisiva": 18,
    "inserção de mídia": 16, "outdoor": 14, "busdoor": 14, "mídia": 12,
    "marketing": 10, "veiculação": 8, "relações públicas": 8, "anúncio": 6,
}

LOGO_SVG_BRANCA = '<img src="https://handson.tec.br/static/img/logo/logo-branca.png" height="40">'

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family:'Space Grotesk',sans-serif !important; background-color:{BG} !important; color:{TEXTO}; }}
.stApp {{ background-color:{BG} !important; }}
.block-container {{ background-color:{BG} !important; padding-top:1rem !important; max-width:1400px; }}
.stApp > header, [data-testid="stHeader"] {{ background:transparent !important; }}
p, span, div, label {{ font-family:'Space Grotesk',sans-serif !important; }}
h1,h2,h3,h4 {{ font-family:'Space Grotesk',sans-serif !important; font-weight:700 !important; color:{TEXTO} !important; }}
.stButton > button {{ background:{SURFACE2} !important; color:{MUTED} !important; border:1px solid {BORDA} !important; border-radius:8px !important; font-weight:500 !important; font-size:13px !important; }}
.stButton > button:hover {{ background:{BORDA} !important; color:{TEXTO} !important; opacity:1 !important; }}
[data-testid="stDownloadButton"] button {{ background:{AZUL} !important; color:white !important; border:none !important; border-radius:8px !important; font-weight:600 !important; }}
[data-testid="stDownloadButton"] button:hover {{ opacity:0.82 !important; }}
div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="column"]:first-child .stButton > button {{ background:{AZUL} !important; color:white !important; border:none !important; font-weight:600 !important; }}
[data-baseweb="select"] {{ background:{SURFACE2} !important; border-radius:8px !important; border:1px solid {BORDA} !important; }}
[data-baseweb="select"] * {{ color:{TEXTO} !important; }}
[data-baseweb="popover"] ul {{ background:{SURFACE2} !important; }}
[data-baseweb="popover"] li {{ background:{SURFACE2} !important; color:{TEXTO} !important; }}
[data-baseweb="popover"] li:hover {{ background:{BORDA} !important; }}
.stTextInput input, .stNumberInput input {{ background:{SURFACE2} !important; border:1px solid {BORDA} !important; border-radius:8px !important; color:{TEXTO} !important; }}
.stSelectbox label,.stTextInput label,.stNumberInput label,.stCheckbox label {{ font-size:10px !important; font-weight:700 !important; text-transform:uppercase !important; letter-spacing:0.1em !important; color:{MUTED} !important; }}
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:{BG}; }}
::-webkit-scrollbar-thumb {{ background:{BORDA}; border-radius:3px; }}
hr {{ border-color:{BORDA} !important; }}
.kpi-strip {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:18px; }}
.kpi-item {{ background:{SURFACE}; border:1px solid {BORDA}; border-top:3px solid {AZUL}; border-radius:12px; padding:14px 16px; flex:1; min-width:120px; text-align:center; }}
.kpi-label {{ font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:{MUTED}; margin-bottom:6px; }}
.kpi-value {{ font-size:28px; font-weight:700; color:{AZUL}; line-height:1.1; }}
.lic-card {{ background:{SURFACE}; border:1px solid {BORDA}; border-radius:14px; margin-bottom:12px; overflow:hidden; }}
.lic-card:hover {{ border-color:{AZUL_MID}; }}
.card-priority {{ display:grid; grid-template-columns:1.4fr 0.7fr 0.7fr 1.6fr 1.4fr; border-bottom:1px solid {BORDA}; }}
.card-field {{ padding:12px 16px; border-right:1px solid {BORDA}; }}
.card-field:last-child {{ border-right:none; }}
.card-field-label {{ font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:{MUTED}; margin-bottom:4px; }}
.card-field-value {{ font-size:14px; font-weight:700; color:{TEXTO}; line-height:1.3; }}
.card-footer {{ padding:10px 16px; display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }}
.card-objeto {{ font-size:12px; font-weight:400; color:{MUTED}; line-height:1.5; flex:1; }}
.card-badges {{ display:flex; gap:6px; align-items:center; flex-shrink:0; flex-wrap:wrap; justify-content:flex-end; }}
.badge {{ display:inline-block; border-radius:20px; padding:2px 9px; font-size:10px; font-weight:600; background:{SURFACE2}; color:{MUTED}; border:1px solid {BORDA}; }}
</style>
""", unsafe_allow_html=True)


# ── Funções ───────────────────────────────────────────────────────────────────

def calcular_score(row):
    texto = f"{row.get('objeto','') or ''} {row.get('palavras_encontradas','') or ''}".lower()
    score = sum(w for kw, w in SCORE_WEIGHTS.items() if kw in texto)
    mod = str(row.get("modalidade","") or "").lower()
    if "concurso"       in mod: score += 15
    elif "concorrência" in mod: score += 8
    elif "pregão"       in mod: score += 5
    if str(row.get("fonte","")) == "PNCP": score += 5
    try:
        if float(row.get("valor_estimado") or 0) > 0: score += 5
    except Exception:
        pass
    return min(int(score), 99)

def score_color(s): return VERDE if s >= 70 else AMARELO if s >= 50 else VERMELHO
def n_agencias(v):
    if v <= 0:         return "—"
    if v < 100_000:    return "1–2"
    if v < 500_000:    return "2–5"
    if v < 2_000_000:  return "3–8"
    if v < 10_000_000: return "5–15"
    return "10+"

def dias_restantes(ts):
    if pd.isna(ts): return None
    try:
        d = ts.date() if hasattr(ts, "date") else ts
        return (d - date.today()).days
    except Exception:
        return None

def prazo_html(ts):
    d = dias_restantes(ts)
    if d is None: return f"<span style='color:{MUTED}'>—</span>"
    if d < 0:     return f"<span style='color:{VERMELHO};font-weight:700'>Encerrado</span>"
    if d == 0:    return f"<span style='color:{VERMELHO};font-weight:700'>Hoje!</span>"
    if d <= 5:    return f"<span style='color:{VERMELHO};font-weight:700'>⚠ {d}d</span>"
    if d <= 15:   return f"<span style='color:{AMARELO};font-weight:700'>⏳ {d}d</span>"
    return              f"<span style='color:{VERDE};font-weight:700'>✓ {d}d</span>"

def excel_bytes(df_):
    cols = ["score","valor_estimado","n_agencias","uf","municipio",
            "orgao","objeto","modalidade","data_encerramento","fonte","link"]
    cols = [c for c in cols if c in df_.columns]
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_[cols].to_excel(w, index=False, sheet_name="Licitações")
        ws = w.sheets["Licitações"]
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(
                max(len(str(c.value or "")) for c in col) + 4, 60)
    return buf.getvalue()


# ── Google Sheets ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def carregar_do_sheets(_gc, planilha_nome, aba_nome):
    ws    = _gc.open(planilha_nome).worksheet(aba_nome)
    dados = ws.get_all_records(default_blank="")
    if not dados: return pd.DataFrame()
    df = pd.DataFrame(dados).fillna("")
    df["score"]      = df.apply(calcular_score, axis=1)
    df["valor_num"]  = pd.to_numeric(df.get("valor_estimado",""), errors="coerce").fillna(0)
    df["n_agencias"] = df["valor_num"].apply(n_agencias)
    if "data_publicacao"   in df.columns: df["data_pub"] = pd.to_datetime(df["data_publicacao"],   errors="coerce")
    if "data_encerramento" in df.columns: df["data_enc"] = pd.to_datetime(df["data_encerramento"], errors="coerce")
    return df.sort_values("score", ascending=False).reset_index(drop=True)

def conectar_sheets():
    if "gc" not in st.session_state:
        if not GSPREAD_OK: raise RuntimeError("gspread não instalado")
        if "credentials" in st.secrets:
            raw = dict(st.secrets["credentials"])
            raw["private_key"] = raw["private_key"].replace("\\n", "\n")
        elif CREDENTIALS_PATH.exists():
            with open(CREDENTIALS_PATH) as f: raw = json.load(f)
        else:
            raise FileNotFoundError("Credenciais não encontradas.")
        st.session_state["gc"] = gspread.service_account_from_dict(raw)
    return st.session_state["gc"]


# ── Conectar ──────────────────────────────────────────────────────────────────
df_raw = pd.DataFrame()
with st.spinner("Conectando..."):
    try:
        gc     = conectar_sheets()
        df_raw = carregar_do_sheets(gc, NOME_PLANILHA, NOME_ABA)
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        st.code(traceback.format_exc())
        st.stop()

if df_raw.empty:
    st.warning("Planilha conectada, mas sem dados.")
    st.stop()


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {"f_busca":"","f_uf":"Todos","f_fonte":"Todas","f_mod":"Todas",
              "f_valor_min":0,"f_ordem":"Score ↓","f_abertos":True,"pag":1}.items():
    if k not in st.session_state: st.session_state[k] = v


# ── Navbar ────────────────────────────────────────────────────────────────────
col_logo, col_btns = st.columns([5, 3])
with col_logo:
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:14px;padding:8px 0'>"
        f"{LOGO_SVG_BRANCA}"
        f"<div><div style='font-size:15px;font-weight:700;color:{TEXTO}'>Radar de Licitações</div>"
        f"<div style='font-size:11px;color:{MUTED}'>Setor de Publicidade · Ampla</div></div></div>",
        unsafe_allow_html=True)
with col_btns:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("↻ Recarregar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with b2:
        st.download_button("⬇️ Excel", data=excel_bytes(df_raw),
            file_name=f"licitacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    with b3:
        st.download_button("⬇️ CSV",
            data=df_raw.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            file_name=f"licitacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv", use_container_width=True)

st.divider()


# ── Filtros ───────────────────────────────────────────────────────────────────
ufs    = ["Todos"] + sorted([u for u in df_raw["uf"].dropna().unique() if u])
fontes = ["Todas"] + sorted([f for f in df_raw["fonte"].dropna().unique() if f])
mods   = ["Todas"] + sorted([m for m in df_raw["modalidade"].dropna().unique() if m])
ordem_opcoes = {"Score ↓":("score",False),"Valor ↓":("valor_num",False),"Prazo ↑":("data_enc",True),"Pub. ↓":("data_pub",False)}

if st.session_state["f_uf"]    not in ufs:    st.session_state["f_uf"]    = "Todos"
if st.session_state["f_fonte"] not in fontes: st.session_state["f_fonte"] = "Todas"
if st.session_state["f_mod"]   not in mods:   st.session_state["f_mod"]   = "Todas"

def reset_pag(): st.session_state["pag"] = 1

f1,f2,f3,f4,f5,f6,f7 = st.columns([2,1,1,1,1,1,1])
with f1: st.text_input("🔍 Buscar", placeholder="objeto ou órgão...", key="f_busca", on_change=reset_pag)
with f2: st.selectbox("📍 UF", ufs, index=ufs.index(st.session_state["f_uf"]), key="f_uf", on_change=reset_pag)
with f3: st.selectbox("📰 Fonte", fontes, index=fontes.index(st.session_state["f_fonte"]), key="f_fonte", on_change=reset_pag)
with f4: st.selectbox("📋 Modalidade", mods, index=mods.index(st.session_state["f_mod"]), key="f_mod", on_change=reset_pag)
with f5: st.number_input("💰 Valor mín (R$)", min_value=0, step=50_000, key="f_valor_min", on_change=reset_pag)
with f6: st.selectbox("↕️ Ordenar", list(ordem_opcoes.keys()), index=list(ordem_opcoes.keys()).index(st.session_state["f_ordem"]), key="f_ordem", on_change=reset_pag)
with f7:
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    st.checkbox("🟢 Só abertos", key="f_abertos", on_change=reset_pag)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ── Aplicar filtros ───────────────────────────────────────────────────────────
df = df_raw.copy()
if st.session_state["f_busca"]:
    b = st.session_state["f_busca"].lower()
    mask = (df["objeto"].str.lower().str.contains(b, na=False) |
            df.get("orgao", pd.Series(dtype=str)).str.lower().str.contains(b, na=False))
    df = df[mask]
if st.session_state["f_uf"]    != "Todos":  df = df[df["uf"]        == st.session_state["f_uf"]]
if st.session_state["f_fonte"] != "Todas":  df = df[df["fonte"]      == st.session_state["f_fonte"]]
if st.session_state["f_mod"]   != "Todas":  df = df[df["modalidade"] == st.session_state["f_mod"]]
if st.session_state["f_valor_min"] > 0:     df = df[df["valor_num"]  >= st.session_state["f_valor_min"]]
if st.session_state["f_abertos"] and "data_enc" in df.columns:
    df = df[df["data_enc"].isna() | (df["data_enc"] >= pd.Timestamp(date.today()))]

ord_col, ord_asc = ordem_opcoes[st.session_state["f_ordem"]]
if ord_col in df.columns:
    df = df.sort_values(ord_col, ascending=ord_asc, na_position="last")
df    = df.reset_index(drop=True)
total = len(df)


# ── KPIs ─────────────────────────────────────────────────────────────────────
valor_total = df["valor_num"].sum()
altos       = int((df["score"] >= 70).sum())
ufs_n       = df["uf"].nunique()
if "data_enc" in df.columns:
    dl = [d for d in (dias_restantes(r) for r in df["data_enc"]) if d is not None and d >= 0]
    prazo_med = f"{int(sum(dl)/len(dl))}d" if dl else "—"
else:
    prazo_med = "—"

total_fmt = f"{total:,}".replace(",",".")
valor_fmt = f"R$ {valor_total/1e6:.1f}M" if valor_total > 0 else "—"

st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi-item"><div class="kpi-label">Resultados</div><div class="kpi-value">{total_fmt}</div></div>
  <div class="kpi-item"><div class="kpi-label">Valor Total</div><div class="kpi-value">{valor_fmt}</div></div>
  <div class="kpi-item"><div class="kpi-label">Score Alto ≥70</div><div class="kpi-value" style="color:{VERDE}">{altos}</div></div>
  <div class="kpi-item"><div class="kpi-label">Estados</div><div class="kpi-value">{ufs_n}</div></div>
  <div class="kpi-item"><div class="kpi-label">Prazo Médio</div><div class="kpi-value" style="color:{AMARELO}">{prazo_med}</div></div>
</div>
""", unsafe_allow_html=True)


# ── Paginação — estado ────────────────────────────────────────────────────────
POR_PAG = 20
n_pags  = max(1, -(-total // POR_PAG))
if st.session_state["pag"] > n_pags:
    st.session_state["pag"] = 1
pag    = st.session_state["pag"]
inicio = (pag - 1) * POR_PAG
fim    = min(inicio + POR_PAG, total)
df_pag = df.iloc[inicio:fim]


# ── Cards ─────────────────────────────────────────────────────────────────────
if total == 0:
    st.markdown(f"<div style='text-align:center;padding:3rem;color:{MUTED}'>Nenhuma licitação encontrada.</div>", unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style='display:grid;grid-template-columns:1.4fr 0.7fr 0.7fr 1.6fr 1.4fr;
                padding:6px 16px;background:{SURFACE2};border:1px solid {BORDA};
                border-radius:8px 8px 0 0;border-bottom:none'>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{AZUL}'>💰 Valor</div>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{AZUL}'>🏢 Agências</div>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{AZUL}'>📍 Local</div>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{AZUL}'>🏛️ Órgão</div>
      <div style='font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{AZUL}'>⏱ Prazo</div>
    </div>
    """, unsafe_allow_html=True)

    for _, r in df_pag.iterrows():
        sc      = int(r.get("score", 0))
        cor     = score_color(sc)
        vn      = float(r.get("valor_num", 0) or 0)
        uf      = str(r.get("uf", "") or "—")
        mun     = str(r.get("municipio", "") or "")
        orgao   = str(r.get("orgao", "") or "")[:55]
        objeto  = str(r.get("objeto", "") or "")[:200]
        mod     = str(r.get("modalidade", "") or "")
        fonte   = str(r.get("fonte", "") or "")
        link    = str(r.get("link", "") or "")
        enc     = r.get("data_enc", None)
        enc_str = str(r.get("data_encerramento", "") or "")[:16]
        pub_str = str(r.get("data_publicacao", "") or "")[:10]
        valor_disp = f"R$ {vn:,.0f}".replace(",",".") if vn > 0 else "A definir"
        local_sub  = f"<br><span style='font-size:11px;color:{MUTED}'>{mun}</span>" if mun and mun.lower() != uf.lower() else ""
        link_html  = (f'<a href="{link}" target="_blank" style="background:{AZUL};color:white;border-radius:6px;padding:4px 12px;font-size:11px;font-weight:600;text-decoration:none">Ver edital →</a>') if link else ""

        st.markdown(f"""
        <div class="lic-card" style="border-left:4px solid {cor}">
          <div class="card-priority">
            <div class="card-field"><div class="card-field-label">💰 Valor estimado</div><div class="card-field-value" style="color:{VERDE}">{valor_disp}</div></div>
            <div class="card-field"><div class="card-field-label">🏢 Agências</div><div class="card-field-value" style="color:{AZUL_MID}">{r.get("n_agencias","—")}</div></div>
            <div class="card-field"><div class="card-field-label">📍 Local</div><div class="card-field-value">{uf}{local_sub}</div></div>
            <div class="card-field"><div class="card-field-label">🏛️ Órgão contratante</div><div class="card-field-value" style="font-size:12px;font-weight:600">{orgao}</div></div>
            <div class="card-field"><div class="card-field-label">⏱ Prazo de entrega</div><div class="card-field-value">{prazo_html(enc)}<div style="font-size:11px;color:{MUTED};font-weight:400;margin-top:2px">{enc_str}</div></div></div>
          </div>
          <div class="card-footer">
            <div class="card-objeto">{objeto}{"..." if len(objeto)==200 else ""}</div>
            <div class="card-badges">
              <span style="background:{cor}20;color:{cor};border:1px solid {cor}50;border-radius:6px;padding:2px 9px;font-size:12px;font-weight:700">{sc}</span>
              <span class="badge">{mod}</span><span class="badge">{fonte}</span>
              <span style="font-size:10px;color:{MUTED}">Pub. {pub_str}</span>
              {link_html}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── Paginação numérica ────────────────────────────────────────────────────────
if n_pags > 1:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    vis   = sorted({1, n_pags, *range(max(1, pag-2), min(n_pags, pag+2)+1)})
    itens = []
    prev  = None
    for p in vis:
        if prev is not None and p - prev > 1:
            itens.append(None)
        itens.append(p)
        prev = p

    _, col_pag, _ = st.columns([2, len(itens)+2, 2])
    with col_pag:
        pcols = st.columns([0.7] + [0.6] * len(itens) + [0.7])

        with pcols[0]:
            if st.button("←", key="prev", disabled=(pag <= 1), use_container_width=True):
                st.session_state["pag"] = pag - 1
                st.rerun()

        for i, item in enumerate(itens):
            with pcols[i + 1]:
                if item is None:
                    st.markdown(f"<div style='text-align:center;color:{MUTED};padding-top:8px'>…</div>", unsafe_allow_html=True)
                elif item == pag:
                    st.markdown(
                        f"<div style='text-align:center;background:{AZUL};color:white;"
                        f"border-radius:8px;padding:7px 0;font-weight:700;font-size:13px'>{item}</div>",
                        unsafe_allow_html=True)
                else:
                    if st.button(str(item), key=f"p{item}", use_container_width=True):
                        st.session_state["pag"] = item
                        st.rerun()

        with pcols[-1]:
            if st.button("→", key="next", disabled=(pag >= n_pags), use_container_width=True):
                st.session_state["pag"] = pag + 1
                st.rerun()

    st.markdown(
        f"<div style='text-align:center;font-size:11px;color:{MUTED};margin-top:4px'>"
        f"Página {pag} de {n_pags} · {total_fmt} resultados</div>",
        unsafe_allow_html=True)


st.divider()
st.markdown(
    f"<div style='font-size:11px;color:{MUTED};text-align:center;padding-bottom:1rem'>"
    f"Ampla · {total_fmt} de {len(df_raw):,} editais · Cache 5 min · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    f"</div>".replace(",","."),
    unsafe_allow_html=True)
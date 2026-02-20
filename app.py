import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re
import unicodedata

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA", page_icon="🎬", layout="wide")

# --- 2. CSS FINAL (BLINDADO CONTRA ERROS DE CÓPIA) ---
css_code = (
    "<style>\n"
    ".stApp { background-color: #ffffff !important; }\n"
    "div.stButton > button { background-color: #000000 !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; }\n"
    "div.stButton > button:hover { background-color: #333333 !important; color: #ffffff !important; }\n"
    "div.stButton > button p { color: #ffffff !important; }\n"
    "h1, h2, h3, h4, h5, h6, .stMarkdown p, .stMarkdown li, label, div { color: #000000 !important; }\n"
    ".stTextInput input { color: #000000 !important; background-color: #ffffff !important; border: 1px solid #ccc !important; }\n"
    "::placeholder { color: #888888 !important; font-style: italic !important; opacity: 1 !important; }\n"
    ".titulo-tech { font-family: 'Helvetica', sans-serif; color: #000000 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 5px; line-height: 1.0; letter-spacing: -1px; }\n"
    ".subtitulo-tech { font-family: 'Helvetica', sans-serif; color: #444444 !important; font-size: 1.2rem; margin-bottom: 25px; }\n"
    ".box-instrucao { background-color: #f0f7ff !important; padding: 15px; border-radius: 8px; border-left: 6px solid #0066cc; color: #333333 !important; font-size: 1rem; margin-bottom: 30px; }\n"
    ".destaque-tech { font-weight: bold; color: #0066cc !important; }\n"
    ".book-card { background: white !important; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }\n"
    ".book-card b, .book-card span { color: #000000 !important; }\n"
    ".ai-card { background-color: #f8f9fa !important; border-left: 5px solid #333; padding: 15px; border-radius: 5px; margin-top: 15px; color: #000000 !important; }\n"
    "@media (max-width: 768px) { .titulo-tech { font-size: 2.5rem !important; } }\n"
    "</style>"
)
st.markdown(css_code, unsafe_allow_html=True)

# --- 3. DADOS E FUNÇÕES ---
def normalizar_texto(texto):
    if not isinstance(texto, str): return str(texto).lower()
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

@st.cache_data
def carregar_dados():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not arquivos: return None
    try:
        df_bruto = pd.read_excel(arquivos[0], header=None)
        inicio = 0
        for i, row in df_bruto.head(15).iterrows():
            if any(x in str(row.values).lower() for x in ['título', 'autor']):
                inicio = i; break
        df = pd.read_excel(arquivos[0], header=inicio)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')].dropna(how='all').fillna('').astype(str)
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        if col_cat: df[col_cat] = df[col_cat].apply(lambda x: re.sub(r'\+.*', '', str(x)).strip())
        return df
    except: return None

df = carregar_dados()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.secrets.get("GOOGLE_API_KEY")
    modelo_escolhido = None
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            nomes_limpos = [m.replace('models/', '') for m in modelos]
            st.success("✅ Online")
            modelo_escolhido = st.selectbox("Motor IA:", nomes_limpos, index=0)
        except: st.error("Erro Conexão")
    
    st.divider()
    if df is not None:
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Filtrar Área:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st

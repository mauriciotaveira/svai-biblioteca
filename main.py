import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# Estilo para os cartões e botões
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .book-card {
        background: white; padding: 20px; border-radius: 10px;
        border: 1px solid #e0e0e0; margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stButton>button { background-color: #000; color: white; border-radius: 6px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA (Elimina o +1 e sujeira do topo)
@st.cache_data
def carregar_dados():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not arquivos: return None
    arquivo = arquivos[0]
    try:
        df_bruto = pd.read_excel(arquivo, header=None)
        inicio = 0
        for i, row in df_bruto.head(15).iterrows():
            linha = row.astype(str).str.lower().tolist()
            if any(x in linha for x in ['título', 'titulo', 'autor']):
                inicio = i; break
        
        df = pd.read_excel(arquivo, header=inicio)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')].dropna(how='all').fillna('').astype(str)
        
        # Limpa o "+1" das categorias
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        if col_cat:
            df[col_cat] = df[col_cat].apply(lambda x: re.sub(r'\+.*', '', str(x)).strip())
        return df
    except: return None

df = carregar_dados()

# 3. INTERFACE PRINCIPAL
st.title("Acervo Cinema & Artes")

if df is not None:
    # Sidebar
    with st.sidebar:
        st.header("Filtros")
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Categoria:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st.metric("Total", len(df))

    df_exibicao = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    tab1, tab2 = st.tabs(["🔍 Busca Visual", "🤖 Consultor IA"])

    with tab1:
        termo = st.text_input("O que você procura?", placeholder="Ex: montagem cinema")
        if termo:
            palavras = [p for p in termo.lower().split() if p not in ['o','a','de','do','em','sobre']]
            mask = df_exibicao.apply(lambda row: all(p in row.astype(str).str.lower().str.cat(sep=' ') for p in palavras), axis=1)
            res = df_exibicao[mask]
        else: res = df_exibicao

        if not res.empty:
            for _, row in res.iterrows():
                # Identifica colunas
                c_tit = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
                c_aut = next((c for c in df.columns if 'autor' in c.lower()), "")
                c_res = next((c for c in df.columns if 'resumo' in c.lower()), "")
                c_ct = next((c for c in df.columns if 'categoria' in c.lower()), "")
                
                st.markdown(f"""<div class="book-card">
                    <div style="display:flex; justify-content:space-between;"><b>{row[c_tit]}</b><span style="font-size:12px; color:gray;">{row[c_ct]}</span></div>
                    <div style="font-size:14px; color:blue;">{row[c_aut]}</div>
                    <div style="font-size:15px; margin-top:8px;">{row[c_res]}</div>
                </div>""", unsafe_allow_html=True)
        else: st.warning("Nada encontrado.")

    # --- ABA 2: CONSULTOR IA (VERSÃO FORÇADA PARA GEMINI-PRO) ---
    with tab2:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        pgt = st.text_input("Sua pergunta:")
        if st.button("Consultar"):
            if "GOOGLE_API_KEY" in st.secrets:
                try:
                    # Configura a chave
                    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                    
                    # TENTATIVA COM GEMINI-PRO (Mais estável para este erro 404)
                    model = genai.GenerativeModel('gemini-pro')
                    
                    # Prepara contexto
                    ctx = res.head(30).to_string(index=False) if termo and not res.empty else df_exibicao.head(40).to_string(index=False)
                    
                    prompt = f"Baseado nestes livros: {ctx}. Responda objetivamente à pergunta: {pgt}"
                    
                    with st.spinner("IA processando..."):
                        resp = model.generate_content(prompt)
                        st.info(resp.text)
                except Exception as e:
                    st.error(f"Erro persistente: {e}")
                    st.warning("Se o erro 404 continuar, é uma falha de cache do Streamlit. Tente mudar o nome do arquivo no GitHub para app_v2.py e reconectar.")
            else:
                st.error("Chave API não configurada nos Secrets.")
else:
    st.error("Arquivo de dados não encontrado.")
import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# 2. CARREGAMENTO E LIMPEZA DE DADOS
@st.cache_data
def carregar_dados():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not arquivos: return None
    arquivo = arquivos[0]
    try:
        df = pd.read_excel(arquivo, header=None)
        inicio = 0
        for i, row in df.head(15).iterrows():
            linha = row.astype(str).str.lower().tolist()
            if any(x in linha for x in ['título', 'titulo', 'autor']):
                inicio = i; break
        
        df = pd.read_excel(arquivo, header=inicio)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')].dropna(how='all').fillna('').astype(str)
        
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        if col_cat:
            df[col_cat] = df[col_cat].apply(lambda x: re.sub(r'\+.*', '', str(x)).strip())
        return df
    except: return None

df = carregar_dados()

# 3. INTERFACE
st.title("Acervo Cinema & Artes")

if df is not None:
    # Barra Lateral
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
                c_tit = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
                c_aut = next((c for c in df.columns if 'autor' in c.lower()), None)
                c_res = next((c for c in df.columns if 'resumo' in c.lower()), None)
                c_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
                
                st.markdown(f"""<div style="background:white; padding:20px; border-radius:10px; border:1px solid #e0e0e0; margin-bottom:15px;">
                    <div style="display:flex; justify-content:space-between;"><b style="font-size:18px;">{row[c_tit]}</b><span style="background:#eee; padding:2px 8px; border-radius:10px; font-size:12px;">{row[c_cat] if c_cat else ''}</span></div>
                    <div style="color:#666; font-style:italic; font-size:14px;">{row[c_aut] if c_aut else ''}</div>
                    <div style="margin-top:10px; color:#333;">{row[c_res] if c_res else ''}</div>
                </div>""", unsafe_allow_html=True)
        else: st.warning("Nada encontrado.")

    # --- ABA DA IA COM CORREÇÃO DE VERSÃO ---
    with tab2:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        pgt = st.text_input("Sua pergunta:")
        if st.button("Consultar"):
            if "GOOGLE_API_KEY" in st.secrets:
                try:
                    # FORÇANDO A VERSÃO DA API PARA EVITAR O ERRO 404
                    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                    
                    # Usamos o modelo 'gemini-1.5-flash' explicitamente
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    ctx = res.head(30).to_string(index=False) if termo and not res.empty else df_exibicao.head(40).to_string(index=False)
                    
                    # O segredo está aqui: pedindo para a biblioteca gerar o conteúdo
                    resp = model.generate_content(f"Dados do acervo: {ctx}. Pergunta: {pgt}")
                    st.info(resp.text)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
                    st.info("O servidor ainda está tentando usar uma versão antiga. Tente mudar o modelo para 'gemini-pro' no código se este erro persistir.")
            else:
                st.error("Chive não configurada nos Secrets.")
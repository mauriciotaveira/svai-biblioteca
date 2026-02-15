import streamlit as st
import pandas as pd
import requests # Usaremos isso para pular a biblioteca quebrada
import json
import os
import re

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

st.markdown("""
<style>
    .book-card {
        background: white; padding: 20px; border-radius: 10px;
        border: 1px solid #e0e0e0; margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .tag { background: #f0f0f0; padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    .stButton>button { background-color: #000; color: white; border-radius: 6px; width: 100%; height: 45px; }
</style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA
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
        if col_cat:
            df[col_cat] = df[col_cat].apply(lambda x: re.sub(r'\+.*', '', str(x)).strip())
        return df
    except: return None

df = carregar_dados()

# 3. INTERFACE
st.title("Acervo Cinema & Artes")

if df is not None:
    with st.sidebar:
        st.header("🗂️ Filtros")
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Categoria:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st.metric("Total", len(df))

    df_exibicao = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    tab1, tab2 = st.tabs(["🔍 Pesquisa Visual", "🤖 Consultor IA"])

    with tab1:
        termo = st.text_input("Busca Visual:", placeholder="Ex: montagem cinema")
        if termo:
            pals = [p for p in termo.lower().split() if p not in ['o','a','de','do','sobre']]
            mask = df_exibicao.apply(lambda r: all(p in r.astype(str).str.lower().str.cat(sep=' ') for p in pals), axis=1)
            res = df_exibicao[mask]
        else: res = df_exibicao

        st.write(f"Encontrados: {len(res)}")
        for _, row in res.iterrows():
            c_tit = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
            c_aut = next((c for c in df.columns if 'autor' in c.lower()), "")
            c_res = next((c for c in df.columns if 'resumo' in c.lower()), "")
            c_ct = next((c for c in df.columns if 'categoria' in c.lower()), "")
            
            st.markdown(f"""<div class="book-card">
                <div style="display:flex; justify-content:space-between;"><b>{row[c_tit]}</b><span class="tag">{row[c_ct]}</span></div>
                <div style="color:blue; font-size:14px;">{row[c_aut]}</div>
                <div style="font-size:15px; margin-top:5px;">{row[c_res]}</div>
            </div>""", unsafe_allow_html=True)

    with tab2:
        pgt = st.text_input("Pergunta à IA:")
        if st.button("Consultar"):
            if "GOOGLE_API_KEY" in st.secrets:
                chave = st.secrets["GOOGLE_API_KEY"]
                ctx = res.head(20).to_string(index=False)
                prompt = f"Baseado nestes livros do acervo: {ctx}. Responda à pergunta do usuário: {pgt}"
                
                # --- SOLUÇÃO VIA CONEXÃO DIRETA (REST API) ---
                # Isso ignora a biblioteca instalada e vai direto no servidor do Google
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={chave}"
                
                headers = {'Content-Type': 'application/json'}
                data = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                
                try:
                    with st.spinner("Conectando direto ao Google..."):
                        response = requests.post(url, headers=headers, json=data)
                        
                        if response.status_code == 200:
                            resultado = response.json()
                            texto_resposta = resultado['candidates'][0]['content']['parts'][0]['text']
                            st.info(texto_resposta)
                        else:
                            st.error(f"Erro no Google: {response.status_code}")
                            st.code(response.text)
                            
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")
            else:
                st.error("Chave não configurada.")

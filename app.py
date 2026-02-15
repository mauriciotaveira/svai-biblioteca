import streamlit as st
import pandas as pd
import google.generativeai as genai
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

# 2. CONEXÃO SEGURA (Igual ao App Constituição)
api_key = st.secrets.get("GOOGLE_API_KEY")

# 3. CARREGAMENTO E LIMPEZA
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

# 4. INTERFACE
st.title("Acervo Cinema & Artes")

if df is not None:
    # --- BARRA LATERAL (LÓGICA DO LEX-IA) ---
    with st.sidebar:
        st.header("⚙️ Configuração IA")
        
        modelo_escolhido = None
        if api_key:
            try:
                genai.configure(api_key=api_key)
                # LISTA OS MODELOS DISPONÍVEIS (O SEGREDO DO SUCESSO)
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                # Limpa o nome (tira 'models/')
                nomes_limpos = [m.replace('models/', '') for m in modelos]
                
                st.success("✅ Conexão Ativa")
                # Deixa o usuário escolher o modelo que existe na conta dele
                modelo_escolhido = st.selectbox("Escolha o Motor:", nomes_limpos, index=0)
            except Exception as e:
                st.error(f"Erro na Chave: {e}")
        else:
            st.warning("⚠️ Chave API não detectada nos Secrets.")

        st.divider()
        st.header("🗂️ Filtros")
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Categoria:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st.metric("Total", len(df))

    # Filtro
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
                <div style="color:blue;">{row[c_aut]}</div>
                <div style="margin-top:5px;">{row[c_res]}</div>
            </div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        pgt = st.text_input("Sua dúvida:")
        
        if st.button("Consultar"):
            if modelo_escolhido and api_key:
                try:
                    # Usa o modelo selecionado na barra lateral (igual ao Lex-IA)
                    model = genai.GenerativeModel(modelo_escolhido)
                    
                    ctx = res.head(20).to_string(index=False)
                    prompt = f"Você é um bibliotecário especialista. Use estes livros como base: {ctx}. Responda: {pgt}"
                    
                    with st.spinner(f"Processando com {modelo_escolhido}..."):
                        response = model.generate_content(prompt)
                        st.info(response.text)
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Verifique a chave API e selecione um modelo na barra lateral.")
else:
    st.error("Arquivo de dados não encontrado.")

import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re

st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# --- ÁREA DE DIAGNÓSTICO DE ERRO (APAGUE ISTO DEPOIS QUE FUNCIONAR) ---
st.markdown("### 🛠️ PAINEL DE DIAGNÓSTICO DA CHAVE")

if "GOOGLE_API_KEY" in st.secrets:
    chave_recebida = st.secrets["GOOGLE_API_KEY"]
    st.success("✅ SUCESSO: O arquivo Secrets foi lido!")
    st.write(f"A chave carregada começa com: **{chave_recebida[:6]}...**")
    st.write(f"O tamanho total da chave é: **{len(chave_recebida)} caracteres**.")
    
    # Teste real de conexão
    try:
        genai.configure(api_key=chave_recebida)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Teste de conexão.")
        st.success("✅ CONEXÃO COM GOOGLE: Funcionando! A IA respondeu.")
    except Exception as e:
        st.error(f"❌ ERRO DE CONEXÃO: O Secret foi lido, mas a chave foi rejeitada pelo Google.")
        st.warning(f"Mensagem do erro: {e}")
        st.info("Dica: Verifique se sua chave API Key está ativa no Google AI Studio.")
else:
    st.error("❌ FRACASSO: O Streamlit NÃO encontrou a variável 'GOOGLE_API_KEY'.")
    st.info("Verifique se no arquivo TOML você escreveu exatamente: GOOGLE_API_KEY = \"sua-chave\"")

st.markdown("---")
# ----------------------------------------------------------------------

# ESTILO VISUAL
st.markdown("""
<style>
    .book-card {
        background-color: white; padding: 20px; border-radius: 10px;
        border: 1px solid #e0e0e0; margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .book-title { font-size: 20px; font-weight: bold; color: #000; margin-bottom: 5px; }
    .book-meta { font-size: 14px; color: #666; font-style: italic; margin-bottom: 10px; }
    .book-resume { font-size: 15px; line-height: 1.5; color: #333; }
    .tag { background-color: #f0f0f0; padding: 3px 8px; border-radius: 10px; font-size: 12px; font-weight: bold; color: #555; }
    .stButton>button { background-color: #000; color: white; border: none; border-radius: 6px; height: 45px; }
</style>
""", unsafe_allow_html=True)

# CARREGAMENTO E LIMPEZA
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

# INTERFACE
st.title("Acervo Cinema & Artes")

if df is not None:
    with st.sidebar:
        st.header("Filtros")
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Categoria:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st.metric("Total", len(df))

    df_exibicao = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    tab1, tab2 = st.tabs(["🔍 Busca", "🤖 IA"])

    with tab1:
        termo = st.text_input("Busca:", placeholder="Digite os termos...")
        if termo:
            palavras = [p for p in termo.lower().split() if p not in ['o','a','de','do','em']]
            mask = df_exibicao.apply(lambda row: all(p in row.astype(str).str.lower().str.cat(sep=' ') for p in palavras), axis=1)
            res = df_exibicao[mask]
        else: res = df_exibicao

        if not res.empty:
            for _, row in res.iterrows():
                # Definição segura das colunas
                c_tit = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
                c_aut = next((c for c in df.columns if 'autor' in c.lower()), None)
                c_res = next((c for c in df.columns if 'resumo' in c.lower()), None)
                c_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
                
                st.markdown(f"""<div class="book-card">
                    <div style="display:flex; justify-content:space-between;"><div class="book-title">{row[c_tit]}</div><span class="tag">{row[c_cat] if c_cat else ''}</span></div>
                    <div class="book-meta">{row[c_aut] if c_aut else ''}</div>
                    <div class="book-resume">{row[c_res] if c_res else ''}</div>
                </div>""", unsafe_allow_html=True)
        else: st.warning("Nada encontrado.")

    with tab2:
        pgt = st.text_input("Pergunta à IA:")
        if st.button("Enviar"):
            if "GOOGLE_API_KEY" in st.secrets:
                try:
                    ctx = res.head(30).to_string(index=False) if termo and not res.empty else df_exibicao.head(40).to_string(index=False)
                    resp = genai.GenerativeModel('gemini-1.5-flash').generate_content(f"Dados: {ctx}. Pergunta: {pgt}")
                    st.write(resp.text)
                except Exception as e: st.error(f"Erro: {e}")
            else: st.error("Chave não configurada.")
import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO INSTITUCIONAL
st.set_page_config(
    page_title="Acervo Cinema & Artes", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. SEGURANÇA (Garante que api_status sempre exista)
api_status = False
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        api_status = True
    except Exception:
        api_status = False

# 3. MOTOR DE DADOS PROFISSIONAL
@st.cache_data
def carregar_dados():
    arquivos = os.listdir()
    # Prioridade para o Excel que você subiu
    arquivo_excel = [f for f in arquivos if f.endswith(('.xlsx', '.xls'))]
    
    if arquivo_excel:
        try:
            df = pd.read_excel(arquivo_excel[0])
            return df, arquivo_excel[0]
        except Exception as e:
            return None, f"Erro ao ler Excel: {e}"
    
    return None, "Aguardando arquivo biblioteca.xlsx"

df, nome_arquivo = carregar_dados()

# 4. ESTILO VISUAL (Design Limpo)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    .stApp { background-color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .block-container { max-width: 1000px !important; margin: 0 auto; padding-top: 2rem; }
    div.stButton > button {
        background-color: #000 !important; color: #fff !important;
        height: 48px; font-weight: bold; border-radius: 6px; width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# 5. INTERFACE
st.title("Acervo Cinema & Artes")
st.caption(f"Base de Dados: {nome_arquivo}")

if df is not None:
    df.columns = df.columns.str.strip()
    tab_busca, tab_ia = st.tabs(["🔍 Pesquisa", "🤖 Consultor IA"])

    with tab_busca:
        termo = st.text_input("Busca no Acervo", placeholder="Digite algo...")
        if st.button("PESQUISAR"):
            if termo:
                mask = df.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
                res = df[mask]
                st.dataframe(res, use_container_width=True, hide_index=True)
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_ia:
        # Aqui é onde o erro NameError acontecia. Agora api_status está definida acima!
        if not api_status:
            st.error("🔒 Chave API não configurada no servidor.")
        else:
            pergunta = st.text_input("Pergunta para o Consultor:")
            if st.button("ANALISAR"):
                with st.spinner("Analisando..."):
                    try:
                        contexto = df.head(100).to_string(index=False)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        resp = model.generate_content(f"Acervo: {contexto}. Pergunta: {pergunta}")
                        st.markdown(resp.text)
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO VISUAL (Limpa e Profissional)
st.set_page_config(
    page_title="Acervo Cinema & Artes", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. CONEXÃO SEGURA COM A IA
# Usamos try/except para garantir que o site não quebre se a chave der erro
api_status = False
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        api_status = True
    except Exception as e:
        api_status = False

# 3. MOTOR DE DADOS (Blindado para Excel)
@st.cache_data
def carregar_dados():
    # Procura o arquivo Excel na pasta
    arquivos_excel = [f for f in os.listdir() if f.endswith('.xlsx')]
    
    if arquivos_excel:
        try:
            # Pega o primeiro Excel que encontrar (biblioteca.xlsx)
            arquivo = arquivos_excel[0]
            df = pd.read_excel(arquivo)
            return df, arquivo
        except Exception as e:
            return None, f"Erro ao ler arquivo: {e}"
    
    return None, "Nenhum arquivo .xlsx encontrado."

df, nome_arquivo = carregar_dados()

# 4. ESTILO CSS (Esconde menus desnecessários)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    .stApp { background-color: #FFFFFF; font-family: sans-serif; }
    .block-container { max-width: 950px !important; margin: 0 auto; padding-top: 2rem; }
    /* Estilo do Botão de Pesquisa */
    div.stButton > button {
        background-color: #000 !important; 
        color: #fff !important; 
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 5. INTERFACE PRINCIPAL
st.title("Acervo Cinema & Artes")

if df is not None:
    # Limpeza preventiva dos dados (remove espaços extras nas colunas)
    df.columns = df.columns.astype(str).str.strip()
    
    # Abas de Navegação
    tab_busca, tab_ia = st.tabs(["🔍 Pesquisa no Acervo", "🤖 Consultor IA"])

    # --- ABA 1: A PESQUISA "TIPO GOOGLE" (VERSÃO 9) ---
    with tab_busca:
        st.write("") # Espaço vazio
        # Campo único que busca em Título, Autor, Ano, etc.
        termo = st.text_input("Pesquisar no acervo:", placeholder="Digite título, autor ou assunto...")
        
        if st.button("PESQUISAR"):
            if termo:
                # LÓGICA DA VERSÃO 9: Transforma tudo em texto e busca o termo
                # 'case=False' ignora maiúsculas/minúsculas
                mask = df.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
                resultado = df[mask]
                
                if not resultado.empty:
                    st.success(f"{len(resultado)} itens encontrados.")
                    st.dataframe(resultado, use_container_width=True, hide_index=True)
                else:
                    st.warning("Nenhum item encontrado com esse termo.")
            else:
                # Se não digitar nada, mostra a tabela toda
                st.dataframe(df, use_container_width=True, hide_index=True)

    # --- ABA 2: CONSULTOR IA ---
    with tab_ia:
        if not api_status:
            st.error("⚠️ A IA não está ativa. Verifique a chave API nos Secrets.")
        else:
            st.info("Pergunte ao Bibliotecário Virtual sobre o conteúdo dos livros.")
            pergunta = st.text_input("Sua pergunta:")
            
            if st.button("ENVIAR PERGUNTA"):
                if pergunta:
                    with st.spinner("Lendo o acervo e formulando resposta..."):
                        try:
                            # Trocamos para o modelo 'gemini-1.5-flash' ou 'gemini-pro'
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            # Limitamos o contexto para não exceder limites rápidos
                            contexto = df.head(60).to_string(index=False)
                            
                            prompt = f"Você é um bibliotecário especialista. Use estes dados do acervo: {contexto}. Responda à pergunta do usuário: {pergunta}"
                            
                            response = model.generate_content(prompt)
                            st.markdown(f"### 🤖 Resposta:\n{response.text}")
                        except Exception as e:
                            st.error(f"Erro na comunicação com a IA: {e}")
                            st.caption("Tente reformular a pergunta ou aguarde alguns instantes.")
else:
    st.error("⚠️ Base de dados não carregada.")
    st.info(f"Status: {nome_arquivo}")
    st.markdown("Certifique-se de que o arquivo **biblioteca.xlsx** está na raiz do GitHub.")
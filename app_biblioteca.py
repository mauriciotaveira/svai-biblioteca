import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# 2. SEGURANÇA
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. MOTOR DE DADOS (FORÇANDO O EXCEL)
@st.cache_data
def carregar_dados():
    # Ignoramos o CSV problemático e vamos direto no Excel profissional
    try:
        if os.path.exists('biblioteca.xlsx'):
            df = pd.read_excel('biblioteca.xlsx')
            return df, 'biblioteca.xlsx'
    except Exception as e:
        st.error(f"Erro ao ler biblioteca.xlsx: {e}")
    
    return None, None

df, nome_arquivo = carregar_dados()

# ... (restante do código de busca e IA)

# 4. DESIGN CSS (Visual Limpo - Coluna Única)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    .stApp { background-color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .block-container { max-width: 1000px !important; margin: 0 auto; padding-top: 2rem; }
    
    /* Inputs e Tabelas */
    input[type="text"] { color: #000 !important; }
    [data-testid="stDataFrame"] { border: 1px solid #eee; border-radius: 10px; }
    
    /* Botão Preto Profissional */
    div.stButton > button {
        background-color: #000 !important; color: #fff !important;
        height: 48px; font-weight: bold; border-radius: 6px; width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# 5. INTERFACE DO USUÁRIO
st.markdown(f"<h1>Acervo Cinema & Artes</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color: #666;'>Base de Dados: <b>{nome_arquivo}</b></p>", unsafe_allow_html=True)

if df is not None:
    # Limpeza de dados (remove espaços vazios)
    df.columns = df.columns.str.strip()
    
    tab_busca, tab_ia = st.tabs(["🔍 Pesquisa no Acervo", "🤖 Consultor IA"])

    with tab_busca:
        st.write("")
        termo = st.text_input("Busca Inteligente", placeholder="Digite título, autor, ano ou palavra-chave...")
        
        if st.button("EXECUTAR PESQUISA"):
            if termo:
                # Busca em todo o DataFrame de forma eficiente
                mask = df.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
                resultado = df[mask]
                
                if not resultado.empty:
                    st.success(f"Foram encontrados {len(resultado)} registros.")
                    st.dataframe(resultado, use_container_width=True, hide_index=True)
                else:
                    st.warning("Nenhum item localizado com este termo.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_ia:
        if not api_status:
            st.error("🔒 O Consultor IA não detectou a chave de segurança no servidor.")
        else:
            st.info("💡 Faça perguntas complexas sobre o acervo (Ex: Quais livros tratam de teoria da imagem?)")
            pergunta = st.text_input("Sua pergunta para o Consultor:")
            
            if st.button("SOLICITAR ANÁLISE"):
                if pergunta:
                    with st.spinner("O Consultor sVAI está analisando os dados..."):
                        try:
                            # Prepara uma amostra dos dados para a IA (Top 100 linhas)
                            amostra_acervo = df.head(100).to_string(index=False)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = f"""
                            Você é o Consultor sVAI, um bibliotecário especialista em Cinema e Artes.
                            Responda à pergunta: '{pergunta}'
                            Use como base principal os seguintes itens do nosso acervo:
                            {amostra_acervo}
                            
                            Responda de forma profissional, elegante e em português.
                            """
                            
                            resposta = model.generate_content(prompt)
                            st.markdown("---")
                            st.markdown(f"### 🤖 Resposta do Consultor:\n\n{resposta.text}")
                        except Exception as e:
                            st.error(f"Erro na análise da IA: {e}")
                else:
                    st.warning("Por favor, digite uma pergunta.")

else:
    st.error(f"⚠️ Erro ao carregar base de dados: {nome_arquivo}")
    st.info("Verifique se o arquivo está na mesma pasta do código e se o nome termina com .xlsx")
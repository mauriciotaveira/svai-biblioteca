import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Cine.IA - Biblioteca", layout="wide")

# Estilo para manter o padrão que você gosta
st.markdown("""
<style>
    .book-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 16px; }
    .stButton>button { background-color: #000; color: white; border-radius: 8px; width: 100%; height: 45px; }
</style>
""", unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    try:
        # Lendo o arquivo que o robô atualizou
        df = pd.read_excel("biblioteca.xlsx")
        df.columns = df.columns.str.strip()
        return df.fillna("---")
    except Exception as e:
        st.error(f"Erro ao ler Excel: {e}")
        return None

df = carregar_dados()

# --- TÍTULO ---
st.title("🎬 Cine.IA - Acervo de Cinema")

if df is not None:
    # --- AS ABAS QUE VOCÊ QUERIA ---
    tab1, tab2 = st.tabs(["🔎 Procurar Livros", "🤖 Assistente de Produção"])

    with tab1:
        st.subheader("Consultar Acervo")
        busca = st.text_input("Digite o que procura (Título, Autor ou Assunto):")
        
        # Filtro de busca
        if busca:
            mask = df.apply(lambda r: busca.lower() in str(r.values).lower(), axis=1)
            res = df[mask]
        else:
            res = df.head(10)

        for _, row in res.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="book-card">
                    <h3 style="margin:0;">{row.get('Título', '---')}</h3>
                    <p style="color:blue;"><b>Autor:</b> {row.get('Autor', '---')} | <b>Editora:</b> {row.get('Editora', '---')}</p>
                    <p><b>Resumo:</b> {row.get('Resumo', '---')}</p>
                    <div style="background:#f9f9f9; padding:10px; border-radius:5px; border-left:4px solid black;">
                        <b>📍 Catalogação:</b> CDD {row.get('CDD', '---')} | <b>Cutter:</b> {row.get('Número de chamada', '---')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.subheader("Assistente de Produção")
        pergunta = st.text_area("Como a IA pode ajudar na sua produção hoje?")
        
        if st.button("Consultar IA"):
            # Tenta pegar a chave de dois jeitos para não dar erro
            api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("google_api_key")
            
            if not api_key:
                st.error("Chave API não encontrada nos Secrets do Streamlit.")
            elif not pergunta:
                st.warning("Por favor, digite uma pergunta.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash') # Versão mais estável
                    
                    # Contexto para a IA (limitado para não travar)
                    contexto = df[['Título', 'Autor', 'Resumo']].head(50).to_string()
                    prompt = f"Você é um assistente de produção cinematográfica. Baseado nestes livros:\n{contexto}\n\nPergunta: {pergunta}"
                    
                    with st.spinner("IA processando..."):
                        response = model.generate_content(prompt)
                        st.info(f"**Resposta do Assistente:**\n\n{response.text}")
                except Exception as e:
                    st.error(f"Erro na API do Google: {e}")
else:
    st.warning("Arquivo biblioteca.xlsx não encontrado.")

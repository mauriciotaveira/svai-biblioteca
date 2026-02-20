import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA - Gestão de Acervo", layout="wide")

st.markdown("""
<style>
    /* Cartão do Livro */
    .book-card {
        background: white; padding: 18px; border-radius: 10px;
        border: 1px solid #e0e0e0; margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); min-height: 260px;
    }
    .cdd-box {
        background-color: #f8f9fa; padding: 8px; border-radius: 5px;
        font-family: monospace; font-size: 12px; color: #1a1a1a;
        border-left: 4px solid #000; margin-top: 10px;
    }
    .abnt-text { font-size: 10px; color: #555; margin-top: 10px; font-style: italic; }
    
    /* Guia de Navegação - Fundo Neutro e Texto Escuro */
    .guide-box { 
        background-color: #f0f2f6; 
        padding: 20px; 
        border-radius: 8px; 
        border: 1px solid #ccc; 
        color: #1a1a1a; 
        margin-bottom: 20px; 
    }

    /* BOTÕES: Corrigindo para o texto não sumir ao clicar */
    .stButton>button { 
        background-color: #000 !important; 
        color: #ffffff !important; 
        border-radius: 8px; 
        width: 100%; 
        border: none;
        font-weight: bold;
    }
    .stButton>button:active, .stButton>button:focus, .stButton>button:hover {
        background-color: #333 !important;
        color: #ffffff !important;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CARREGAR DADOS ---
@st.cache_data
def load_data():
    if not os.path.exists("biblioteca.xlsx"): return None
    df = pd.read_excel("biblioteca.xlsx")
    df.columns = df.columns.str.strip()
    return df.fillna("")

df = load_data()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")
    st.info("Motor: Gemini 2.5 Flash") 
    st.divider()
    if df is not None:
        st.metric("Obras no Acervo", len(df))

st.title("🎬 Cine.IA - Acervo de Cinema")

if df is not None:
    tab1, tab2 = st.tabs(["🤖 Assistente de Produção", "🔎 Buscar Livros"])

    with tab1:
        st.markdown("""
        <div class="guide-box">
            <strong>Como navegar no Assistente:</strong><br>
            • Deseja tirar dúvidas teóricas sobre o acervo?<br>
            • Digite uma pergunta sobre cinema, autores ou conceitos técnicos?<br>
            • Quer que a IA consulte a base de dados para uma resposta fundamentada?
        </div>
        """, unsafe_allow_html=True)
        
        pergunta = st.text_area("Sua consulta:", placeholder="Ex: Quais livros tratam de semiótica no cinema?")
        
        if st.button("Obter Resposta Técnica"):
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key and pergunta:
                try:
                    genai.configure(api_key=api_key)
                    # Chamada para o modelo 2.5 Flash (ajustado para a API de 2026)
                    model = genai.GenerativeModel('gemini-2.5-flash') 
                    contexto = df[['Título', 'Autor', 'Resumo']].head(60).to_string()
                    response = model.generate_content(f"Acervo: {contexto}\nPergunta: {pergunta}")
                    st.info(response.text)
                except Exception as e: 
                    st.error(f"Erro na conexão com o Motor 2.5: {e}")

    with tab2:
        st.markdown("""
        <div class="guide-box">
            <strong>Como realizar sua pesquisa?</strong><br>
            • Procurando por um título específico?<br>
            • Deseja filtrar as obras por nome de autor?<br>
            • Precisa encontrar livros por palavras-chave ou temas?
        </div>
        """, unsafe_allow_html=True)
        
        col_busca, col_btn = st.columns([3, 1])
        with col_busca:
            busca = st.text_input("Campo de busca:", placeholder="Digite aqui...", label_visibility="collapsed")
        with col_btn:
            btn_buscar = st.button("Executar Busca")
        
        # Só exibe os livros se o botão for clicado e houver texto
        if btn_buscar and busca:
            mask = df.apply(lambda r: busca.lower() in str(r.values).lower(), axis=1)
            resultados = df[mask]
            
            if not resultados.empty:
                st.write(f"Encontrados: {len(resultados)} livros")
                cols = st.columns(2)
                for i, (index, row) in enumerate(resultados.iterrows()):
                    # Lógica ABNT (SOBRENAME, Nome. Título. Editora, Ano/s.d.)
                    autor_raw = str(row.get('Autor', '')).strip()
                    titulo = str(row.get('Título', ''))
                    editora = str(row.get('Editora', ''))
                    data = str(row.get('Ano', '')).strip()
                    if not data or data == "nan" or data == "": data = "s.d."

                    if autor_raw:
                        partes = autor_raw.split()
                        sobrenome = partes[-1].upper()
                        nome_resto = " ".join(partes[:-1])
                        citacao = f"{sobrenome}, {nome_resto}. **{titulo}**. {editora}, {data}."
                    else:
                        citacao = f"AUTOR DESCONHECIDO. **{titulo}**. {editora}, {data}."

                    with cols[i % 2]:
                        st.markdown(f"""
                            <div class="book-card">
                                <h4 style="margin:0; color:#000;">{titulo}</h4>
                                <p style="color:blue; font-size:14px; margin-top:5px;">{autor_raw}</p>
                                <p style="font-size:13px; color:#1a1a1a;">{row.get('Resumo', '')[:280]}...</p>
                                <div class="cdd-box">
                                    📍 CDD {row.get('CDD', '---')} | Chamada: {row.get('Número de chamada', '---')}
                                </div>
                                <div class="abnt-text">Ref: {citacao}</div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("Nenhum resultado encontrado para este termo.")
else:
    st.error("Arquivo biblioteca.xlsx não carregado.")

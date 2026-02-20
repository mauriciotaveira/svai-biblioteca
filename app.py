import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA - Gestão de Acervo", layout="wide")

st.markdown("""
<style>
    /* Fundo geral da página para evitar temas automáticos ruins */
    .stApp { background-color: #ffffff; }

    /* Cartão do Livro com alto contraste */
    .book-card {
        background: #ffffff; padding: 20px; border-radius: 12px;
        border: 1px solid #d1d1d1; margin-bottom: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .book-card h4 { color: #000000 !important; margin: 0; }
    .book-card p { color: #1a1a1a !important; line-height: 1.6; }

    /* Caixa de Resposta da IA - FUNDO CINZA NEUTRO, FONTE ESCURA */
    .ai-response-box {
        background-color: #f0f2f6 !important; 
        color: #000000 !important; 
        padding: 25px; 
        border-radius: 10px; 
        border: 1px solid #ced4da;
        line-height: 1.8;
        font-size: 16px;
        margin-top: 20px;
    }

    /* Guia de Navegação */
    .guide-box { 
        background-color: #f8f9fa; 
        padding: 20px; 
        border-radius: 8px; 
        border: 1px solid #dee2e6; 
        color: #212529; 
        margin-bottom: 25px; 
    }

    /* Botões Pretos com texto Branco fixo */
    .stButton>button { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        font-weight: bold;
        border: none;
        padding: 10px 20px;
    }
    
    /* CDD e ABNT */
    .cdd-box {
        background-color: #e9ecef; padding: 10px; border-radius: 6px;
        font-family: 'Courier New', Courier, monospace; font-size: 13px; color: #000;
        border-left: 5px solid #000; margin-top: 12px;
    }
    .abnt-text { font-size: 11px; color: #444; margin-top: 12px; }
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
        st.metric("Total de Obras", len(df))

st.title("🎬 Cine.IA - Acervo de Cinema")

if df is not None:
    tab1, tab2 = st.tabs(["🤖 Assistente de Produção", "🔎 Buscar Livros"])

    with tab1:
        st.markdown("""
        <div class="guide-box">
            <strong>Como navegar no Assistente:</strong><br>
            • Deseja uma análise profunda baseada no acervo?<br>
            • Digite sua pergunta sobre teoria, técnica ou história do cinema.<br>
            • O sistema redigirá um texto técnico e fundamentado utilizando os livros disponíveis.
        </div>
        """, unsafe_allow_html=True)
        
        pergunta = st.text_area("Sua consulta técnica:", height=150, placeholder="Ex: Explique o processo de montagem e sua importância narrativa...")
        
        if st.button("Obter Resposta Técnica"):
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key and pergunta:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash') 
                    contexto = df[['Título', 'Autor', 'Resumo', 'Ano']].head(100).to_string()
                    
                    # PROMPT MELHORADO PARA EVITAR LISTAS SUPERFICIAIS
                    prompt_final = f"""
                    Você é um especialista em cinema e bibliotecário sênior.
                    Baseado EXCLUSIVAMENTE no acervo abaixo, responda à pergunta do usuário.
                    IMPORTANTE: Não faça apenas uma lista de tópicos. Escreva um texto longo, fluido, dissertativo e profundo. 
                    Encadeie as ideias dos autores (como Eisenstein, Murch e Amiel) para explicar os conceitos.
                    Cite as obras ao longo do texto de forma elegante.
                    
                    Acervo: {contexto}
                    Pergunta: {pergunta}
                    """
                    
                    with st.spinner("Analisando acervo e redigindo resposta..."):
                        response = model.generate_content(prompt_final)
                        st.markdown(f'<div class="ai-response-box">{response.text}</div>', unsafe_allow_html=True)
                except Exception as e: 
                    st.error(f"Erro na conexão com o Motor 2.5: {e}")

    with tab2:
        st.markdown("""
        <div class="guide-box">
            <strong>Como realizar sua pesquisa?</strong><br>
            • Procurando por um título, autor ou tema?<br>
            • Digite o termo abaixo e clique em Executar Busca.<br>
            • Os resultados aparecerão em cartões detalhados com referência ABNT.
        </div>
        """, unsafe_allow_html=True)
        
        col_busca, col_btn = st.columns([3, 1])
        with col_busca:
            busca = st.text_input("Campo de busca:", placeholder="Digite aqui...", label_visibility="collapsed")
        with col_btn:
            btn_buscar = st.button("Executar Busca")
        
        if btn_buscar and busca:
            mask = df.apply(lambda r: busca.lower() in str(r.values).lower(), axis=1)
            resultados = df[mask]
            
            if not resultados.empty:
                cols = st.columns(2)
                for i, (index, row) in enumerate(resultados.iterrows()):
                    # Lógica ABNT com s.d.
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
                                <h4>{titulo}</h4>
                                <p style="color:#0000FF !important; font-weight:bold;">{autor_raw}</p>
                                <p style="font-size:14px;">{row.get('Resumo', '')}</p>
                                <div class="cdd-box">
                                    📍 CDD {row.get('CDD', '---')} | Chamada: {row.get('Número de chamada', '---')}
                                </div>
                                <div class="abnt-text">Ref: {citacao}</div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("Nenhum resultado encontrado.")

else:
    st.error("Arquivo biblioteca.xlsx não carregado.")

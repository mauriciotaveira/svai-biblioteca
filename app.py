import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA - Gestão de Acervo", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    
    .book-card {
        background: #ffffff; padding: 20px; border-radius: 12px;
        border: 1px solid #d1d1d1; margin-bottom: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
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

    .guide-box { 
        background-color: #f8f9fa; padding: 20px; border-radius: 8px; 
        border: 1px solid #dee2e6; color: #212529; margin-bottom: 25px; 
    }

    .stButton>button { 
        background-color: #000000 !important; color: #ffffff !important; 
        font-weight: bold; border: none; padding: 10px 20px; width: 100%;
    }
    .stButton>button:active, .stButton>button:focus, .stButton>button:hover {
        background-color: #333333 !important; color: #ffffff !important; border: none;
    }
    
    .cdd-box {
        background-color: #e9ecef; padding: 10px; border-radius: 6px;
        font-family: monospace; font-size: 13px; color: #000;
        border-left: 5px solid #000; margin-top: 12px;
    }
    .abnt-text { font-size: 11px; color: #444; margin-top: 12px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CARREGAR DADOS ---
@st.cache_data
def load_data():
    if not os.path.exists("biblioteca.xlsx"): return None
    try:
        df = pd.read_excel("biblioteca.xlsx")
        df.columns = df.columns.str.strip()
        return df.fillna("")
    except: return None

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

    # ==========================================
    # ABA 1: ASSISTENTE COM BUSCA INTELIGENTE
    # ==========================================
    with tab1:
        st.markdown("""
        <div class="guide-box">
            <strong>Como navegar no Assistente:</strong><br>
            • Deseja uma análise profunda baseada no acervo?<br>
            • Digite sua pergunta sobre teoria, técnica ou história do cinema.<br>
            • O sistema redigirá um texto técnico e fundamentado utilizando os livros disponíveis.
        </div>
        """, unsafe_allow_html=True)
        
        pergunta = st.text_area("Sua consulta técnica:", height=150)
        
        if st.button("Obter Resposta Técnica"):
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key and pergunta:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash') 
                    
                    # --- FILTRO INTELIGENTE PARA NÃO ESTOURAR A COTA ---
                    # 1. Pega as palavras da sua pergunta maiores que 3 letras
                    palavras_chave = [p.lower() for p in pergunta.replace("?", "").replace(",", "").split() if len(p) > 3]
                    
                    # 2. Busca no Excel inteiro apenas os livros que tenham essas palavras
                    if palavras_chave:
                        mask = df.apply(lambda r: any(p in str(r.values).lower() for p in palavras_chave), axis=1)
                        df_relevante = df[mask]
                    else:
                        df_relevante = df.head(0)
                    
                    # 3. Se achou poucos, completa com os primeiros para dar volume
                    if len(df_relevante) < 5:
                        df_relevante = pd.concat([df_relevante, df.head(15)]).drop_duplicates()
                    
                    # 4. Limita a 20 obras altamente focadas para mandar para a IA
                    colunas_disponiveis = [c for c in ['Título', 'Autor', 'Resumo', 'Editora', 'Ano'] if c in df.columns]
                    contexto = df_relevante[colunas_disponiveis].head(20).to_string()
                    
                    # --- O PROMPT MESTRE ---
                    prompt_final = f"""
                    Você é um especialista em cinema. Responda à pergunta do usuário baseado APENAS no acervo fornecido abaixo.
                    
                    DIRETRIZES IMPORTANTES:
                    1. ESTILO E TOM: Seja elegante, acessível e direto. Evite jargões excessivamente acadêmicos ou saudações pedantes (nunca use "Caríssimo pesquisador" ou similar).
                    2. ESTRUTURA: Escreva um texto longo, fluido, dissertativo e profundo. Discorra sobre o tema conectando as ideias dos autores presentes no acervo. NÃO faça listas de tópicos.
                    3. PRIORIDADE: Foque primeiro nas obras que tratam diretamente do assunto solicitado (ex: se o usuário perguntar sobre Film Noir, use as obras que citam isso diretamente antes de teorizar).
                    4. REFERÊNCIAS ABNT: É OBRIGATÓRIO que o último elemento da sua resposta seja uma seção chamada "Referências Citadas", listando TODAS as obras que você usou no texto no formato ABNT (SOBRENOME, Nome. Título. Editora, Ano.). Se o ano não existir, use s.d.
                    
                    Acervo selecionado para esta pergunta: 
                    {contexto}
                    
                    Pergunta: {pergunta}
                    """
                    
                    with st.spinner("Mapeando acervo e redigindo ensaio..."):
                        response = model.generate_content(prompt_final)
                        st.markdown(f'<div class="ai-response-box">{response.text}</div>', unsafe_allow_html=True)
                except Exception as e: 
                    st.error(f"Erro na conexão com a API: {e}")

    # ==========================================
    # ABA 2: BUSCA MANUAL E VISUAL DE DUAS COLUNAS
    # ==========================================
    with tab2:
        st.markdown("""
        <div class="guide-box">
            <strong>Como realizar sua pesquisa?</strong><br>
            • Procurando por um título, autor ou tema?<br>
            • Digite o termo abaixo e clique em Executar Busca.
        </div>
        """, unsafe_allow_html=True)
        
        col_busca, col_btn = st.columns([3, 1])
        with col_busca:
            busca = st.text_input("Campo de busca:", label_visibility="collapsed")
        with col_btn:
            btn_buscar = st.button("Executar Busca")
        
        if btn_buscar and busca:
            mask = df.apply(lambda r: busca.lower() in str(r.values).lower(), axis=1)
            resultados = df[mask]
            
            if not resultados.empty:
                cols = st.columns(2)
                for i, (index, row) in enumerate(resultados.iterrows()):
                    titulo = row.get('Título', 'Sem Título')
                    autor_raw = row.get('Autor', '')
                    editora = row.get('Editora', 's.n.')
                    ano = row.get('Ano', row.get('Data', 's.d.'))
                    if not str(ano).strip(): ano = "s.d."

                    if autor_raw:
                        partes = str(autor_raw).split()
                        sobrenome = partes[-1].upper()
                        nome_resto = " ".join(partes[:-1])
                        citacao = f"{sobrenome}, {nome_resto}. **{titulo}**. {editora}, {ano}."
                    else:
                        citacao = f"AUTOR DESCONHECIDO. **{titulo}**. {editora}, {ano}."

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

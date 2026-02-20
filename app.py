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
    # ABA 1: ASSISTENTE COM RANKING DE RELEVÂNCIA
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
                    
                    # --- FILTRO POR RANKING (A SOLUÇÃO PARA ACHAR A ORTEGOSA) ---
                    # 1. Ignora palavras comuns e foca nas chaves reais
                    stop_words = ['sobre', 'como', 'qual', 'para', 'pelo', 'esse', 'este', 'isso', 'fale', 'livro']
                    palavras_chave = [p.lower() for p in pergunta.replace("?", "").replace(",", "").split() if len(p) > 3 and p.lower() not in stop_words]
                    
                    df_relevante = df.copy()
                    
                    # 2. Cria um sistema de pontuação: quanto mais a palavra aparece, maior a nota do livro
                    if palavras_chave:
                        df_relevante['Pontuacao'] = df_relevante.apply(
                            lambda r: sum(str(r.values).lower().count(p) for p in palavras_chave), axis=1
                        )
                        # Filtra e ordena do maior para o menor
                        df_relevante = df_relevante[df_relevante['Pontuacao'] > 0].sort_values(by='Pontuacao', ascending=False)
                    else:
                        df_relevante = df_relevante.head(0)
                    
                    # 3. Completa se necessário para não faltar contexto
                    if len(df_relevante) < 5:
                        df_relevante = pd.concat([df_relevante, df.head(15)]).drop_duplicates(subset=['Título'])
                    
                    # 4. Pega os 20 melhores livros rankeados
                    colunas_disponiveis = [c for c in ['Título', 'Autor', 'Resumo', 'Editora', 'Ano'] if c in df.columns]
                    contexto = df_relevante[colunas_disponiveis].head(20).to_string()
                    
                    # --- PROMPT ATUALIZADO ---
                    prompt_final = f"""
                    Você é um especialista em cinema. Responda à pergunta do usuário baseado APENAS no acervo fornecido abaixo.
                    
                    DIRETRIZES IMPORTANTES:
                    1. ESTILO E TOM: Seja elegante, claro e direto. Evite jargões excessivamente acadêmicos ou saudações pedantes (não use "Caríssimo", etc.).
                    2. ESTRUTURA: Escreva um texto longo, fluido, dissertativo e profundo. Conecte as ideias dos autores presentes no acervo. NÃO faça listas de tópicos.
                    3. PRIORIDADE ABSOLUTA: O acervo abaixo já foi filtrado por relevância. As primeiras obras da lista são as mais importantes para o tema. Certifique-se de utilizá-las e citá-las no texto de forma prioritária.
                    4. REFERÊNCIAS ABNT: É OBRIGATÓRIO que o último elemento da sua resposta seja uma seção chamada "Referências Citadas", listando TODAS as obras que você usou no texto no formato ABNT (SOBRENOME, Nome. Título. Editora, Ano.). Se o ano não existir, use s.d.
                    
                    Acervo selecionado para esta pergunta (ordenado por relevância): 
                    {contexto}
                    
                    Pergunta: {pergunta}
                    """
                    
                    with st.spinner("Mapeando as obras mais relevantes e redigindo ensaio..."):
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

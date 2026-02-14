import streamlit as st
import pandas as pd
import google.generativeai as genai
import time

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATÓRIO SER A PRIMEIRA LINHA)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# -----------------------------------------------------------------------------
# 2. CONEXÃO SEGURA COM A IA (LENDO SEU ARQUIVO SECRETS.TOML)
# -----------------------------------------------------------------------------
api_key = None

# Tenta pegar a chave do seu arquivo seguro (.streamlit/secrets.toml)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]

# Configura a IA se a chave foi encontrada
if api_key:
    genai.configure(api_key=api_key)
else:
    # Se não achar, avisa discretamente na lateral
    st.warning("⚠️ Arquivo secrets.toml não detectado ou chave incorreta.")

# -----------------------------------------------------------------------------
# 3. CARREGAMENTO DE DADOS (MOTOR DE ARQUIVOS)
# -----------------------------------------------------------------------------
@st.cache_data
def carregar_dados(arquivo_upload=None):
    # Se o usuário subiu um arquivo agora, usa ele
    if arquivo_upload is not None:
        try:
            if arquivo_upload.name.endswith('.csv'):
                return pd.read_csv(arquivo_upload)
            else:
                return pd.read_excel(arquivo_upload)
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
            return None
    
    # Se não, tenta achar arquivos na pasta do projeto
    try:
        return pd.read_csv("biblioteca.csv")
    except:
        try:
            return pd.read_excel("livros.xlsx")
        except:
            return None

# Tenta carregar automaticamente
df = carregar_dados()

# -----------------------------------------------------------------------------
# 4. ESTILO CSS (DESIGN "CINEMA PRO" - COLUNA ÚNICA E LIMPEZA)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    /* FUNDO BRANCO E FONTE PROFISSIONAL */
    .stApp { background-color: #FFFFFF; color: #1A1A1A; font-family: 'Inter', sans-serif; }
    
    /* REMOVER ESPAÇOS E MENUS DO STREAMLIT */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 3rem !important; }
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}

    /* CORREÇÃO CRÍTICA DE LEGIBILIDADE (PRETO NO BRANCO) */
    input[type="text"], textarea, .stMultiSelect div {
        color: #000000 !important;
        background-color: #FFFFFF !important; 
        border: 1px solid #ced4da !important;
    }
    
    /* BOTÕES PRETOS (ESTILO CINEMA) */
    div.stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        height: 50px !important;
        font-weight: 700 !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* MENU DE NAVEGAÇÃO (TABS) */
    div[role="radiogroup"] {
        background-color: #F8F9FA;
        padding: 8px;
        border-radius: 10px;
        margin-bottom: 25px;
        border: 1px solid #E9ECEF;
        display: flex;
        justify-content: center;
    }
    div[role="radiogroup"] label {
        color: #333 !important;
        font-weight: 600;
        cursor: pointer;
    }

    /* TÍTULO RESPONSIVO */
    h1 { font-size: 2.2rem; color: #000; font-weight: 800; margin: 0; letter-spacing: -1px; }
    p.subtitulo { color: #666; font-size: 1rem; margin-top: 5px; }
    
    @media (max-width: 768px) {
        h1 { font-size: 1.6rem !important; }
        p.subtitulo { font-size: 0.9rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. INTERFACE VISUAL (FRONT-END)
# -----------------------------------------------------------------------------

# Se não achou arquivo automático, mostra botão de upload
if df is None:
    st.markdown("### 📂 Configuração Inicial")
    st.warning("Nenhum arquivo 'biblioteca.csv' ou 'livros.xlsx' encontrado na pasta.")
    arquivo = st.file_uploader("Faça upload da sua planilha agora:", type=["csv", "xlsx"])
    if arquivo:
        df = carregar_dados(arquivo)
        st.rerun() # Recarrega a página ao subir

# Se já temos dados, mostra o app completo
if df is not None:
    
    # Limpeza básica nos nomes das colunas
    df.columns = df.columns.str.strip()
    
    # Identifica a coluna de assuntos/categorias automaticamente
    col_categoria = None
    cols_possiveis = [c for c in df.columns if any(x in c.lower() for x in ['cat', 'assunto', 'area', 'genero'])]
    if cols_possiveis:
        col_categoria = cols_possiveis[0]

    # --- CABEÇALHO ---
    st.markdown("""
        <div style="text-align: left; margin-bottom: 20px;">
            <h1>Acervo Cinema & Artes</h1>
            <p class="subtitulo">Sistema Integrado de Pesquisa e Referência</p>
        </div>
    """, unsafe_allow_html=True)

    # --- NAVEGAÇÃO ---
    modo_uso = st.radio(
        "Menu de Navegação", 
        ["🔍 Pesquisa no Acervo", "🤖 Consultor IA"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # =========================================================================
    # MODO 1: PESQUISA (BUSCA REAL NO EXCEL)
    # =========================================================================
    if modo_uso == "🔍 Pesquisa no Acervo":
        
        # Filtro de Categoria (se existir no excel)
        filtro_cats = []
        if col_categoria:
            st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #333; margin-bottom: 2px;'>FILTRAR CATEGORIAS</p>", unsafe_allow_html=True)
            opcoes_cat = sorted(df[col_categoria].dropna().astype(str).unique())
            filtro_cats = st.multiselect(
                "Categorias", 
                options=opcoes_cat, 
                label_visibility="collapsed",
                placeholder="Selecione os temas..."
            )
            st.write("") # Respiro

        # Filtro de Texto
        st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #333; margin-bottom: 2px;'>TERMO DE BUSCA</p>", unsafe_allow_html=True)
        termo = st.text_input(
            "Busca", 
            placeholder="Digite título, autor ou palavra-chave...", 
            label_visibility="collapsed"
        )
        
        # Botão de Pesquisa
        if st.button("LOCALIZAR OBRA"):
            # Lógica de Filtragem
            resultado = df.copy()
            
            # 1. Aplica filtro de categoria
            if filtro_cats and col_categoria:
                resultado = resultado[resultado[col_categoria].astype(str).isin(filtro_cats)]
            
            # 2. Aplica filtro de texto (busca em todo o dataframe)
            if termo:
                mask = resultado.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
                resultado = resultado[mask]
            
            # Exibe Resultados
            if not resultado.empty:
                st.success(f"Encontramos {len(resultado)} registros.")
                st.dataframe(resultado, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhum item encontrado com esses critérios.")

    # =========================================================================
    # MODO 2: CONSULTOR IA (CONECTADO AO GEMINI)
    # =========================================================================
    elif modo_uso == "🤖 Consultor IA":
        
        st.info("💡 Pergunte ao acervo como se falasse com um bibliotecário sênior.")
        
        st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #333; margin-bottom: 2px;'>SUA PERGUNTA</p>", unsafe_allow_html=True)
        pergunta = st.text_input(
            "Pergunta", 
            placeholder="Ex: Indique livros sobre a estética da fome no Cinema Novo.", 
            label_visibility="collapsed"
        )
        
        if st.button("ANALISAR COM IA"):
            if not api_key:
                st.error("⚠️ Erro de Configuração: API Key não encontrada no secrets.toml.")
            elif not pergunta:
                st.warning("Por favor, digite uma pergunta.")
            else:
                with st.spinner('Consultando o acervo e formulando resposta...'):
                    try:
                        # Prepara o contexto (uma amostra dos livros para a IA ler)
                        # Limitamos a 60 linhas para ser rápido e eficiente
                        contexto_acervo = df.head(60).to_string(index=False)
                        
                        # Prompt Especializado
                        prompt = f"""
                        Você é um Bibliotecário Especialista em Cinema e Artes.
                        Use o seguinte catálogo de livros como base para sua resposta (esta é apenas uma amostra do acervo):
                        ---
                        {contexto_acervo}
                        ---
                        
                        PERGUNTA DO USUÁRIO: "{pergunta}"
                        
                        DIRETRIZES:
                        1. Priorize recomendar livros que ESTÃO na lista acima. Cite Título e Autor.
                        2. Se a lista não tiver livros exatos sobre o tema, use seu conhecimento geral para sugerir clássicos da área, mas DEIXE CLARO que são sugestões externas.
                        3. Responda de forma curta, elegante e acadêmica.
                        """
                        
                        # Chama o Gemini
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(prompt)
                        
                        # Mostra a resposta
                        st.markdown("### 🤖 Resposta do Consultor:")
                        st.markdown(response.text)
                        
                    except Exception as e:
                        st.error(f"Erro de conexão com a IA: {e}")
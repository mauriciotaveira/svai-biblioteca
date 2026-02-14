import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Layout Wide para ocupar tudo, mas limpo)
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# 2. ESTILO CSS (Design Limpo e Menu Unificado)
st.markdown("""
    <style>
    /* FUNDO E FONTE */
    .stApp { background-color: #FFFFFF; color: #1A1A1A; font-family: 'Inter', sans-serif; }
    
    /* REMOVER ESPAÇOS E MENUS PADRÃO */
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}

    /* ESTILO DOS BOTÕES DE NAVEGAÇÃO (RADIO) - Para parecerem abas */
    div[role="radiogroup"] {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 12px;
        display: flex;
        justify-content: center;
        margin-bottom: 25px;
        border: 1px solid #e0e0e0;
    }
    
    div[role="radiogroup"] label {
        background-color: transparent;
        padding: 5px 15px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
    }

    /* BOTÃO DE AÇÃO PRETO (Estilo Cinema) */
    div.stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        height: 50px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }

    /* INPUTS E SELECTS (Visual limpo e clicável) */
    .stTextInput > div > div, .stMultiSelect > div > div {
        border: 1px solid #ced4da;
        border-radius: 8px;
        background-color: #fff;
    }
    
    /* REFORÇO DE COLUNA ÚNICA NO MOBILE */
    @media (max-width: 768px) {
        .stMultiSelect, .stTextInput {
            width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# 3. TÍTULO PRINCIPAL (Apenas este, sem "Classificação via IA")
st.markdown("""
    <div style="text-align: left; margin-bottom: 15px;">
        <h1 style='color: #000; font-size: 2rem; margin: 0; font-weight: 800; letter-spacing: -0.5px;'>
            Acervo Cinema & Artes
        </h1>
        <p style='color: #666; font-size: 1rem; margin-top: 5px;'>
            Sistema Integrado de Pesquisa e Referência
        </p>
    </div>
""", unsafe_allow_html=True)

# 4. NAVEGAÇÃO UNIFICADA (O container cinza com as opções)
modo_uso = st.radio(
    "Navegação", 
    ["🔍 Pesquisa no Acervo", "🤖 Consultor IA"],
    horizontal=True,
    label_visibility="collapsed"
)

# 5. LÓGICA DE EXIBIÇÃO (Sem colunas, tudo empilhado e limpo)

if modo_uso == "🔍 Pesquisa no Acervo":
    
    # SEÇÃO 1: FILTROS (Largura Total)
    st.markdown("<p style='font-size: 0.9rem; font-weight: 700; color: #333; margin-bottom: 5px;'>CATEGORIAS</p>", unsafe_allow_html=True)
    categorias = st.multiselect(
        "Filtro de Categorias",
        options=["Antropologia", "Artes", "Audiovisual", "Cinema", "Ciência Política", "Filosofia", "Fotografia", "Ficção", "Design", "Idioma", "Antropologia", "Marketing", "Economia", "Comunicação"],
        default=None,
        placeholder="Selecione os temas de interesse...",
        label_visibility="collapsed"
    )
    
    st.write("") # Espaço vazio (Respiro)
    
    # SEÇÃO 2: TERMO (Largura Total)
    st.markdown("<p style='font-size: 0.9rem; font-weight: 700; color: #333; margin-bottom: 5px;'>TERMO DE BUSCA</p>", unsafe_allow_html=True)
    termo_busca = st.text_input(
        "Busca",
        placeholder="Digite título, autor ou assunto...",
        label_visibility="collapsed"
    )
    
    st.write("") # Espaço vazio
    
    # BOTÃO
    if st.button("LOCALIZAR OBRA"):
        if not termo_busca and not categorias:
            st.warning("⚠️ Digite um termo ou selecione uma categoria.")
        else:
            # Simulando resultado para visualização
            st.success(f"🔎 Buscando '{termo_busca}'...")

elif modo_uso == "🤖 Consultor IA":
    
    st.info("💡 Este consultor utiliza Inteligência Artificial para responder perguntas complexas sobre o acervo.")
    
    st.markdown("<p style='font-size: 0.9rem; font-weight: 700; color: #333; margin-bottom: 5px;'>SUA PERGUNTA</p>", unsafe_allow_html=True)
    user_question = st.text_input(
        "Pergunta",
        placeholder="Ex: Qual a relação entre o Cinema Novo e a política brasileira?",
        label_visibility="collapsed"
    )
    
    if st.button("ANALISAR COM IA"):
        pass
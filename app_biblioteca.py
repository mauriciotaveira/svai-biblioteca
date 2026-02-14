import streamlit as st
import pandas as pd
import time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# --- DADOS DE EXEMPLO (PARA VOCÊ VER FUNCIONANDO) ---
# Quando for usar seus dados reais, substitua isso pelo seu pd.read_csv(...)
data_exemplo = {
    'Titulo': ['A Estética da Fome', 'Montagem Soviética', 'O Som no Cinema', 'Antropologia Visual', 'História da Arte Moderna'],
    'Autor': ['Glauber Rocha', 'Sergei Eisenstein', 'Michel Chion', 'Claudine de France', 'Gombrich'],
    'Categoria': ['Cinema', 'Cinema', 'Audiovisual', 'Antropologia', 'Artes'],
    'Ano': [1965, 1925, 1990, 1998, 1950]
}
df = pd.DataFrame(data_exemplo)

# 2. ESTILO CSS (CORREÇÃO DE CORES E TAMANHOS)
st.markdown("""
    <style>
    /* FUNDO GERAL BRANCO */
    .stApp { 
        background-color: #FFFFFF; 
        color: #1A1A1A; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* REMOVER ESPAÇOS EXTRAS */
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}

    /* --- CORREÇÃO DO INPUT (TEXTO INVISÍVEL) --- */
    /* Força o texto digitado a ser PRETO e o fundo BRANCO */
    input[type="text"] {
        color: #000000 !important;
        background-color: #FFFFFF !important; 
    }
    
    /* Garante que o texto dentro das caixas de seleção também seja escuro */
    .stMultiSelect div, .stTextInput div {
        color: #000000 !important;
    }
    
    /* TÍTULO RESPONSIVO (Ajuste para Celular) */
    h1.titulo-principal {
        font-size: 2.2rem;
        font-weight: 800;
        color: #000000;
        letter-spacing: -1px;
        margin: 0;
    }
    
    /* No celular, o título diminui para 1.5rem (24px) */
    @media (max-width: 768px) {
        h1.titulo-principal {
            font-size: 1.5rem !important;
        }
        .subtitulo {
            font-size: 0.9rem !important;
        }
    }

    /* ESTILO DOS BOTÕES DE NAVEGAÇÃO (TABS) */
    div[role="radiogroup"] {
        background-color: #F0F2F6;
        padding: 8px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #E0E0E0;
    }
    div[role="radiogroup"] label {
        color: #333333 !important; /* Cor do texto das abas */
        font-weight: 600;
    }

    /* BOTÃO DE AÇÃO PRETO */
    div.stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        height: 50px !important;
        font-weight: 700 !important;
        width: 100%;
        text-transform: uppercase;
        margin-top: 15px;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
    }
    
    /* Feedback de Sucesso/Erro */
    .stAlert {
        background-color: #f8f9fa;
        color: #333;
        border: 1px solid #ddd;
    }
    </style>
""", unsafe_allow_html=True)

# 3. CABEÇALHO
st.markdown("""
    <div style="text-align: left; margin-bottom: 15px;">
        <h1 class="titulo-principal">
            Acervo Cinema & Artes
        </h1>
        <p class="subtitulo" style='color: #555; font-size: 1rem; margin-top: 5px;'>
            Sistema Integrado de Pesquisa e Referência
        </p>
    </div>
""", unsafe_allow_html=True)

# 4. NAVEGAÇÃO
modo_uso = st.radio(
    "Navegação", 
    ["🔍 Pesquisa no Acervo", "🤖 Consultor IA"],
    horizontal=True,
    label_visibility="collapsed"
)

# 5. LÓGICA (COM AÇÃO REAL)

if modo_uso == "🔍 Pesquisa no Acervo":
    
    st.markdown("**CATEGORIAS**")
    categorias = st.multiselect(
        "Filtro de Categorias",
        options=df['Categoria'].unique(), # Pega categorias do dataframe falso
        default=None,
        placeholder="Selecione...",
        label_visibility="collapsed"
    )
    
    st.write("") 
    
    st.markdown("**TERMO DE BUSCA**")
    termo_busca = st.text_input(
        "Busca",
        placeholder="Digite título ou autor...",
        label_visibility="collapsed"
    )
    
    # LÓGICA REAL DO BOTÃO
    if st.button("LOCALIZAR OBRA"):
        # Mostra um spinner para parecer que está processando
        with st.spinner('Buscando no acervo...'):
            time.sleep(0.5) # Pequena pausa dramática
            
            # Filtra o DataFrame de exemplo
            resultados = df.copy()
            
            # Filtro 1: Categoria
            if categorias:
                resultados = resultados[resultados['Categoria'].isin(categorias)]
            
            # Filtro 2: Texto
            if termo_busca:
                resultados = resultados[
                    resultados['Titulo'].str.contains(termo_busca, case=False) | 
                    resultados['Autor'].str.contains(termo_busca, case=False)
                ]
            
            # Exibe resultado
            if not resultados.empty:
                st.success(f"Encontramos {len(resultados)} itens.")
                st.dataframe(resultados, use_container_width=True, hide_index=True)
            else:
                st.error("Nenhum item encontrado com esses filtros.")

elif modo_uso == "🤖 Consultor IA":
    
    st.info("💡 Pergunte ao acervo como se falasse com um bibliotecário.")
    
    st.markdown("**SUA PERGUNTA**")
    user_question = st.text_input(
        "Pergunta",
        placeholder="Ex: Livros sobre montagem soviética...",
        label_visibility="collapsed"
    )
    
    if st.button("ANALISAR COM IA"):
        if user_question:
            with st.spinner('O Consultor sVAI está analisando...'):
                time.sleep(1.5) # Simula tempo de pensamento da IA
                
                # Resposta Simulada (Aqui entraria o código do Gemini)
                st.markdown(f"""
                ### 🤖 Análise do Consultor
                
                Para sua pesquisa sobre **"{user_question}"**, recomendo iniciar pelos clássicos do formalismo russo.
                
                **Sugestões de Leitura:**
                1. *A Forma do Filme* - Sergei Eisenstein
                2. *O Sentido do Filme* - Sergei Eisenstein
                
                > **Nota Técnica:** A montagem soviética prioriza o conflito dialectico entre planos, ao contrário da montagem invisível de Hollywood.
                """)
        else:
            st.warning("Por favor, digite uma pergunta.")
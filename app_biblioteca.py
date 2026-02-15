import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO VISUAL PROFISSIONAL
st.set_page_config(
    page_title="Acervo Cinema & Artes",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS para remover bordas feias e deixar elegante
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    /* Esconde índices de tabelas */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    /* Botões pretos elegantes */
    .stButton>button {
        background-color: #111;
        color: white;
        border-radius: 4px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA DE DADOS (O Segredo da Elegância)
@st.cache_data
def carregar_dados():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if arquivos:
        try:
            df = pd.read_excel(arquivos[0])
            
            # --- LIMPEZA VISUAL (Remove colunas 'Unnamed' e linhas vazias) ---
            # Remove colunas que o Excel cria automaticamente (Unnamed: 0, etc)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Substitui 'nan' (erro visual) por texto vazio
            df = df.fillna('')
            
            # Garante que tudo seja texto para a busca funcionar
            df = df.astype(str)
            
            return df, arquivos[0]
        except Exception as e:
            return None, f"Erro: {e}"
    return None, "Aguardando arquivo .xlsx"

df, nome_arquivo = carregar_dados()

# 3. BARRA LATERAL (FILTROS DE CATEGORIA)
with st.sidebar:
    st.header("🗂️ Filtros do Acervo")
    
    if df is not None:
        # Filtro de CATEGORIA (Se existir a coluna)
        cols_lower = [c.lower() for c in df.columns]
        if 'categoria' in cols_lower:
            col_cat = df.columns[cols_lower.index('categoria')]
            categorias = sorted(list(set(df[col_cat].unique())))
            # Remove categorias vazias da lista
            categorias = [c for c in categorias if c != '']
            cat_selecionada = st.selectbox("Filtrar por Categoria", ["Todas"] + categorias)
        else:
            cat_selecionada = "Todas"
            
        st.write("---")
        st.metric("Total de Obras", len(df))
    
    st.info("Desenvolvido por sVAI")

# 4. ÁREA PRINCIPAL
st.title("Acervo Cinema & Artes")

if df is not None:
    # --- APLICAÇÃO DOS FILTROS ---
    df_exibicao = df.copy()
    
    # 1. Filtra por Categoria (Sidebar)
    if cat_selecionada != "Todas":
        col_cat = df.columns[[c.lower() for c in df.columns].index('categoria')]
        df_exibicao = df_exibicao[df_exibicao[col_cat] == cat_selecionada]

    # Abas
    tab_busca, tab_ia = st.tabs(["🔍 Pesquisa no Acervo", "🤖 Consultor IA"])

    # --- ABA 1: BUSCA INTELIGENTE ---
    with tab_busca:
        # Busca textual
        termo = st.text_input("Busca Rápida:", placeholder="Digite título, autor ou assunto...")
        
        if termo:
            # Busca no dataframe já filtrado pela categoria
            mask = df_exibicao.apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            resultado = df_exibicao[mask]
        else:
            resultado = df_exibicao

        # Exibição dos Resultados
        if not resultado.empty:
            st.caption(f"Exibindo {len(resultado)} itens.")
            # hide_index=True esconde a coluna de números da esquerda
            st.dataframe(
                resultado, 
                use_container_width=True, 
                hide_index=True,
                height=500
            )
        else:
            st.warning("Nenhum item encontrado com esses filtros.")

    # --- ABA 2: CONSULTOR IA ---
    with tab_ia:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        
        # Conexão Segura
        if "GOOGLE_API_KEY" in st.secrets:
            try:
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                # Modelo Flash (Rápido)
                model = genai.GenerativeModel('gemini-1.5-flash')
                api_ok = True
            except:
                api_ok = False
        else:
            api_ok = False
            
        if not api_ok:
            st.error("⚠️ IA Indisponível (Verifique a Chave API).")
        else:
            pergunta = st.text_input("Dúvida sobre o conteúdo:", key="ia_query")
            if st.button("Consultar"):
                if pergunta:
                    with st.spinner("Analisando acervo..."):
                        try:
                            # Contexto Inteligente: Usa os dados FILTRADOS
                            # Se você filtrou "Cinema", a IA só lê livros de Cinema
                            contexto = df_exibicao.head(60).to_string(index=False)
                            
                            prompt = f"""
                            Aja como um bibliotecário culto. Use estes dados:
                            {contexto}
                            
                            Responda à pergunta do usuário: "{pergunta}"
                            Se não souber, diga que não consta no acervo atual.
                            """
                            
                            response = model.generate_content(prompt)
                            st.success("Resposta do Bibliotecário:")
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"Erro técnico: {e}")
                            st.caption("Tente reiniciar o App no menu superior direito.")

else:
    st.error("Nenhum arquivo .xlsx encontrado.")
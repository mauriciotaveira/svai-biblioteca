import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. DESIGN VISUAL (CSS para Cartões Elegantes)
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

st.markdown("""
<style>
    /* Remove espaços inúteis no topo */
    .block-container { padding-top: 2rem; }
    
    /* Estilo dos Cartões de Livros */
    .book-card {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 15px;
    }
    .book-title { font-size: 22px; font-weight: bold; color: #111; margin-bottom: 5px;}
    .book-meta { font-size: 14px; color: #666; font-style: italic; margin-bottom: 10px;}
    .book-resume { font-size: 16px; color: #333; line-height: 1.5; }
    
    /* Botão Preto */
    .stButton>button {
        background-color: #000; color: white; border-radius: 5px; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA (Para tirar os 'nan' e 'Table 1')
@st.cache_data
def carregar_acervo():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not arquivos: return None
    
    arquivo = arquivos[0]
    try:
        # Lê o arquivo bruto
        df = pd.read_excel(arquivo, header=None)
        
        # Procura onde começa o cabeçalho real (Título/Autor)
        inicio_real = 0
        for i, row in df.head(10).iterrows():
            linha = row.astype(str).str.lower().tolist()
            if 'título' in linha or 'titulo' in linha or 'autor' in linha:
                inicio_real = i
                break
        
        # Recarrega com o cabeçalho certo
        df = pd.read_excel(arquivo, header=inicio_real)
        
        # Limpeza Pesada
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')] # Remove colunas fantasmas
        df = df.dropna(how='all') # Remove linhas totalmente vazias
        df = df.fillna('') # Remove 'nan' visual
        df = df.astype(str) # Garante texto para busca
        
        return df
    except:
        return None

df = carregar_acervo()

# 3. INTERFACE PRINCIPAL
st.title("Acervo Cinema & Artes")

if df is not None:
    # Barra Lateral
    with st.sidebar:
        st.header("Filtros")
        st.metric("Total de Obras", len(df))
        
        # Filtro de Categoria (se existir)
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_filtro = "Todas"
        if col_cat:
            opcoes = sorted([x for x in df[col_cat].unique() if x])
            cat_filtro = st.selectbox("Categoria:", ["Todas"] + opcoes)

    # Lógica de Filtro
    df_exibicao = df.copy()
    if cat_filtro != "Todas" and col_cat:
        df_exibicao = df_exibicao[df_exibicao[col_cat] == cat_filtro]

    # Abas
    tab1, tab2 = st.tabs(["🔍 Pesquisa Visual", "🤖 Consultor IA"])

    # --- ABA 1: RESULTADOS EM CARTÕES (SEM PLANILHA FEIA) ---
    with tab1:
        termo = st.text_input("Busca Rápida:", placeholder="Digite título, autor ou assunto...")
        
        if termo:
            mask = df_exibicao.apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            resultados = df_exibicao[mask]
        else:
            resultados = df_exibicao

        st.markdown(f"**Exibindo {len(resultados)} obras**")
        st.write("---")

        # AQUI ESTÁ A MUDANÇA: Loop para criar cartões em vez de tabela
        if not resultados.empty:
            for index, row in resultados.iterrows():
                # Tenta achar as colunas certas pelo nome (flexível)
                c_titulo = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
                c_autor = next((c for c in df.columns if 'autor' in c.lower()), None)
                c_resumo = next((c for c in df.columns if 'resumo' in c.lower()), None)
                
                # Monta o HTML do Cartão
                titulo = row[c_titulo]
                autor = row[c_autor] if c_autor else ""
                resumo = row[c_resumo] if c_resumo else ""
                
                html_card = f"""
                <div class="book-card">
                    <div class="book-title">{titulo}</div>
                    <div class="book-meta">{autor}</div>
                    <div class="book-resume">{resumo}</div>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
        else:
            st.warning("Nenhum livro encontrado.")

    # --- ABA 2: CONSULTOR IA (FIXADO) ---
    with tab2:
        if "GOOGLE_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            pergunta = st.text_input("Pergunte ao Bibliotecário:")
            if st.button("Enviar"):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    ctx = df_exibicao.head(50).to_string()
                    res = model.generate_content(f"Dados: {ctx}. Pergunta: {pergunta}")
                    st.info(res.text)
                except Exception as e:
                    st.error(f"Erro: {e}")
                    st.caption("Se der erro 404, delete o App no Streamlit e crie de novo.")
        else:
            st.error("Configure a API Key.")

else:
    st.error("Erro na leitura do arquivo.")
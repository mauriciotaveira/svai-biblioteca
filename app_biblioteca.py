import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. DESIGN VISUAL (CSS)
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .book-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .book-card:hover { border-color: #000; transform: translateY(-2px); }
    .book-title { font-size: 20px; font-weight: 700; color: #111; margin-bottom: 8px; }
    .book-meta { font-size: 14px; color: #555; margin-bottom: 12px; font-family: monospace;}
    .book-resume { font-size: 15px; color: #444; line-height: 1.6; }
    .tag {
        display: inline-block; background-color: #f0f0f0; color: #333;
        padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: 600;
    }
    .stButton>button {
        background-color: #000; color: white; border-radius: 8px; height: 45px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA DE DADOS
@st.cache_data
def carregar_acervo():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not arquivos: return None
    
    arquivo = arquivos[0]
    try:
        # A. Identifica cabeçalho real
        df = pd.read_excel(arquivo, header=None)
        inicio = 0
        for i, row in df.head(15).iterrows():
            linha = row.astype(str).str.lower().tolist()
            if any(x in linha for x in ['título', 'titulo', 'autor']):
                inicio = i
                break
        
        df = pd.read_excel(arquivo, header=inicio)
        
        # B. Limpeza Pesada
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.dropna(how='all')
        df = df.fillna('')
        df = df.astype(str)
        
        # C. Limpeza das Categorias (+1)
        # Procura coluna de categoria e remove tudo após o '+'
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        if col_cat:
            df[col_cat] = df[col_cat].apply(lambda x: str(x).split('+')[0].strip())
            # Remove quem ficou vazio ou 'nan'
            df = df[df[col_cat] != 'nan']
            df = df[df[col_cat] != '']

        return df
    except:
        return None

df = carregar_acervo()

# 3. INTERFACE PRINCIPAL
st.title("Acervo Cinema & Artes")

if df is not None:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("🗂️ Filtros")
        
        # Filtro de Categoria
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_filtro = "Todas"
        if col_cat:
            opcoes = sorted([x for x in df[col_cat].unique() if len(x) > 1])
            cat_filtro = st.selectbox("Categoria:", ["Todas"] + opcoes)
            
        st.metric("Obras no Acervo", len(df))
        st.caption("Desenvolvido por sVAI")

    # Aplica Filtro de Categoria
    df_exibicao = df.copy()
    if cat_filtro != "Todas" and col_cat:
        df_exibicao = df_exibicao[df_exibicao[col_cat] == cat_filtro]

    # Abas
    tab1, tab2 = st.tabs(["🔍 Pesquisa Visual", "🤖 Consultor IA"])

    # --- ABA 1: BUSCA INTELIGENTE (MODO "E") ---
    with tab1:
        st.markdown("##### Busca Rápida:")
        termo_input = st.text_input("", placeholder="Ex: montagem cinema (encontra livros com AMBOS os termos)")
        
        if termo_input:
            # 1. Quebra a frase em palavras
            palavras = termo_input.lower().split()
            # 2. Palavras proibidas (Stopwords) para não buscar "o", "a", "de"
            ignorar = ['o', 'a', 'os', 'as', 'de', 'do', 'da', 'em', 'para', 'com', 'tem', 'livros', 'sobre', 'quero']
            palavras_chave = [p for p in palavras if p not in ignorar]
            
            if not palavras_chave:
                resultados = df_exibicao
            else:
                # 3. LÓGICA "E" (AND): Todas as palavras devem estar na linha
                def contem_todas_palavras(row):
                    texto_linha = row.astype(str).str.lower().str.cat(sep=' ')
                    # Retorna True APENAS se TODAS as palavras chaves estiverem presentes
                    return all(p in texto_linha for p in palavras_chave)
                
                mask = df_exibicao.apply(contem_todas_palavras, axis=1)
                resultados = df_exibicao[mask]
        else:
            resultados = df_exibicao

        # Exibição
        st.markdown(f"Exibindo {len(resultados)} obras")
        st.write("---")

        if not resultados.empty:
            for index, row in resultados.iterrows():
                # Identifica colunas dinamicamente
                c_titulo = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
                c_autor = next((c for c in df.columns if 'autor' in c.lower()), None)
                c_resumo = next((c for c in df.columns if 'resumo' in c.lower()), None)
                c_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
                
                titulo = row[c_titulo]
                autor = row[c_autor] if c_autor else ""
                resumo = row[c_resumo] if c_resumo else ""
                categoria = row[c_cat] if c_cat else ""
                
                # HTML do Cartão
                html = f"""
                <div class="book-card">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div class="book-title">{titulo}</div>
                        <span class="tag">{categoria}</span>
                    </div>
                    <div class="book-meta">{autor}</div>
                    <div class="book-resume">{resumo}</div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
        else:
            st.warning("Nenhum livro encontrado com todos esses termos simultaneamente.")

    # --- ABA 2: CONSULTOR IA ---
    with tab2:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("Chave API não configurada.")
        else:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            pergunta = st.text_input("Qual sua dúvida?", key="input_ia")
            
            if st.button("Consultar IA"):
                if pergunta:
                    with st.spinner("Analisando acervo..."):
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            # Contexto Inteligente: Usa os resultados da busca se houver
                            if termo_input and not resultados.empty:
                                dados_ia = resultados.head(30).to_string(index=False)
                                aviso = f"(Baseado nos {len(resultados)} livros da sua busca)"
                            else:
                                dados_ia = df_exibicao.head(40).to_string(index=False)
                                aviso = "(Baseado no acervo geral)"

                            prompt = f"Use estes livros: {dados_ia}. Responda: {pergunta}"
                            resp = model.generate_content(prompt)
                            
                            st.success(f"Resposta {aviso}:")
                            st.write(resp.text)
                            
                        except Exception as e:
                            st.error("⚠️ Erro de versão da API (404).")
                            st.info("SOLUÇÃO: Delete este App no painel do Streamlit e crie um novo (New App) para limpar o cache do servidor.")

else:
    st.error("Nenhum arquivo Excel carregado.")
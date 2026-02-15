import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re

# 1. DESIGN VISUAL (Mantendo o que você gostou)
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .book-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #eee;
        margin-bottom: 12px;
        transition: transform 0.2s;
    }
    .book-card:hover { transform: scale(1.01); border-color: #ccc; }
    .book-title { font-size: 20px; font-weight: 700; color: #111; margin-bottom: 4px;}
    .book-meta { font-size: 14px; color: #555; margin-bottom: 8px;}
    .book-resume { font-size: 15px; color: #333; line-height: 1.5; }
    .tag {
        display: inline-block; background-color: #e0e0e0; color: #333;
        padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-right: 5px;
    }
    .stButton>button {
        background-color: #000; color: white; border-radius: 6px; width: 100%; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA AVANÇADA
@st.cache_data
def carregar_acervo():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not arquivos: return None
    
    arquivo = arquivos[0]
    try:
        # Acha o cabeçalho real
        df = pd.read_excel(arquivo, header=None)
        inicio = 0
        for i, row in df.head(15).iterrows():
            linha = row.astype(str).str.lower().tolist()
            if any(x in linha for x in ['título', 'titulo', 'autor']):
                inicio = i
                break
        
        df = pd.read_excel(arquivo, header=inicio)
        
        # Limpeza Técnica
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.dropna(how='all')
        df = df.fillna('')
        df = df.astype(str)
        
        # --- NOVO: LIMPEZA DAS CATEGORIAS (+1) ---
        # Procura coluna de categoria e remove números e sinais estranhos
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        if col_cat:
            # Remove " +1", " +2" ou qualquer coisa que não seja texto limpo no final
            df[col_cat] = df[col_cat].apply(lambda x: re.sub(r'\s*\+\d+', '', x).strip())

        return df
    except:
        return None

df = carregar_acervo()

# 3. INTERFACE
st.title("Acervo Cinema & Artes")

if df is not None:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("🗂️ Filtros")
        
        # Filtro de Categoria (Agora limpo)
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_filtro = "Todas"
        if col_cat:
            opcoes = sorted([x for x in df[col_cat].unique() if x and x.lower() != 'nan'])
            cat_filtro = st.selectbox("Categoria:", ["Todas"] + opcoes)
            
        st.metric("Total de Obras", len(df))
        st.info("Dica: A busca agora entende frases como 'livros sobre montagem'.")

    # Aplica Filtro de Categoria
    df_exibicao = df.copy()
    if cat_filtro != "Todas" and col_cat:
        df_exibicao = df_exibicao[df_exibicao[col_cat] == cat_filtro]

    # Abas
    tab1, tab2 = st.tabs(["🔍 Pesquisa Visual", "🤖 Consultor IA"])

    # --- ABA 1: BUSCA INTELIGENTE (SEM ERRO DE FRASE) ---
    with tab1:
        termo_input = st.text_input("Busca Rápida:", placeholder="Ex: livros sobre montagem e edição...")
        
        # Lógica de Busca Inteligente
        if termo_input:
            # 1. Quebra a frase em palavras
            palavras = termo_input.lower().split()
            # 2. Remove palavras inúteis (Stopwords)
            ignorar = ['o', 'a', 'os', 'as', 'de', 'do', 'da', 'em', 'para', 'com', 'tem', 'livro', 'livros', 'sobre', 'quero', 'gostaria', 'se', 'um', 'uma']
            palavras_chave = [p for p in palavras if p not in ignorar]
            
            if not palavras_chave:
                # Se a pessoa só digitou "livros sobre", não busca nada ou busca tudo
                resultados = df_exibicao
            else:
                # 3. Verifica se AS PALAVRAS CHAVE existem na linha (em qualquer ordem)
                def contem_palavras(row):
                    texto_linha = row.astype(str).str.lower().str.cat(sep=' ')
                    # Retorna True se pelo menos uma das palavras chave estiver na linha
                    return any(p in texto_linha for p in palavras_chave)
                
                mask = df_exibicao.apply(contem_palavras, axis=1)
                resultados = df_exibicao[mask]
        else:
            resultados = df_exibicao

        # Exibição
        if not resultados.empty:
            st.caption(f"Encontramos {len(resultados)} obras.")
            
            # Loop dos Cartões
            for index, row in resultados.iterrows():
                # Identifica colunas
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
                    <div style="display:flex; justify-content:space-between;">
                        <div class="book-title">{titulo}</div>
                        <div><span class="tag">{categoria}</span></div>
                    </div>
                    <div class="book-meta">{autor}</div>
                    <div class="book-resume">{resumo}</div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
        else:
            st.warning("Nenhum livro encontrado com essas palavras-chave.")

    # --- ABA 2: CONSULTOR IA (TENTATIVA ROBUSTA) ---
    with tab2:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("Chave API não configurada.")
        else:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            pergunta = st.text_input("Qual sua dúvida?")
            
            if st.button("Consultar"):
                if pergunta:
                    with st.spinner("Lendo acervo..."):
                        try:
                            # Tenta o modelo Flash primeiro
                            try:
                                model = genai.GenerativeModel('gemini-1.5-flash')
                                teste = model.generate_content("Oi") # Teste rápido
                            except:
                                # Se falhar, tenta o Pro (Fallback)
                                model = genai.GenerativeModel('gemini-pro')
                            
                            # Prepara contexto filtrado
                            contexto = df_exibicao.head(40).to_string(index=False)
                            prompt = f"Use estes dados de livros: {contexto}. Responda: {pergunta}"
                            
                            resp = model.generate_content(prompt)
                            st.info(resp.text)
                            
                        except Exception as e:
                            st.error("A IA ainda está instável devido à versão do servidor.")
                            st.code(str(e))
                            st.markdown("**Solução:** É necessário deletar o App no Streamlit e criar de novo.")

else:
    st.error("Erro na leitura do arquivo Excel.")
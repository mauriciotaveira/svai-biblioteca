import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO DA PÁGINA (Layout Wide + Sidebar Colapsada)
st.set_page_config(
    page_title="Acervo Cinema & Artes", 
    layout="wide", 
    initial_sidebar_state="collapsed" # Começa sem barra lateral
)

# 2. SEGURANÇA DA API (Lê APENAS do arquivo oculto)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    api_status = True
else:
    api_status = False 
    # Não mostramos mais campo de input na tela para segurança total.

# 3. MOTOR DE DADOS INTELIGENTE (CORRETOR DE "EXCEL FEIO")
@st.cache_data
def carregar_dados_limpos():
    # Tenta achar arquivos na pasta
    arquivos = [f for f in os.listdir() if f.endswith(('.csv', '.xlsx'))]
    
    if not arquivos:
        return None, "Nenhum arquivo encontrado."
    
    arquivo = arquivos[0] # Pega o primeiro
    df = None
    
    try:
        if arquivo.endswith('.csv'):
            # TENTATIVA 1: Leitura Padrão
            df = pd.read_csv(arquivo)
            
            # DIAGNÓSTICO: Se o Excel ficou "feio" (tudo em 1 coluna), tenta o padrão Brasil
            if df.shape[1] < 2:
                # Recarrega usando ponto e vírgula e encoding Latin1 (Brasil)
                df = pd.read_csv(arquivo, sep=';', encoding='latin1')
                
        else:
            df = pd.read_excel(arquivo)
            
        return df, arquivo
    except Exception as e:
        return None, str(e)

# Carrega os dados
df, info_arquivo = carregar_dados_limpos()

# 4. DESIGN CSS (Esconde Sidebar + Estilo Cinema)
st.markdown("""
    <style>
    /* FUNDO E FONTE */
    .stApp { background-color: #FFFFFF; color: #1A1A1A; font-family: 'Inter', sans-serif; }
    
    /* ESCONDER A BARRA LATERAL (SIDEBAR) TOTALMENTE */
    [data-testid="stSidebar"] { display: none; }
    
    /* Ajustes de Espaçamento */
    .block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; max-width: 900px !important; margin: 0 auto !important; }
    
    /* Esconde Toolbar e Rodapé */
    [data-testid="stToolbar"], footer {visibility: hidden;}

    /* INPUTS (Busca e Pergunta) - PRETO NO BRANCO */
    input[type="text"], textarea, .stMultiSelect div {
        color: #000000 !important;
        background-color: #FAFAFA !important; 
        border: 1px solid #ced4da !important;
    }
    
    /* BOTÕES PRETOS ELEGANTES */
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
    div.stButton > button:hover { background-color: #333 !important; }

    /* MENU DE ESCOLHA (TABS) */
    div[role="radiogroup"] {
        background-color: #F1F3F5;
        padding: 8px;
        border-radius: 8px;
        border: 1px solid #E9ECEF;
        display: flex;
        justify-content: center;
        margin-bottom: 30px;
    }
    div[role="radiogroup"] label {
        color: #333 !important; font-weight: 600; font-size: 16px;
    }
    
    /* TABELA DE DADOS (Mais bonita) */
    [data-testid="stDataFrame"] { border: 1px solid #eee; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# 5. INTERFACE DO USUÁRIO

# Se o carregamento falhou ou não achou arquivo
if df is None:
    st.error(f"⚠️ {info_arquivo}")
    st.info("O sistema não encontrou o arquivo na pasta. Por favor, arraste seu Excel/CSV aqui para começar:")
    # Upload no MEIO da tela (não na sidebar)
    uploaded = st.file_uploader("Upload de Arquivo", type=['csv', 'xlsx'])
    if uploaded:
        try:
            if uploaded.name.endswith('.csv'):
                # Tenta corrigir automaticamente separador brasileiro
                df = pd.read_csv(uploaded, sep=';', encoding='latin1')
                if df.shape[1] < 2: # Se ainda estiver ruim, tenta vírgula
                    uploaded.seek(0)
                    df = pd.read_csv(uploaded, sep=',')
            else:
                df = pd.read_excel(uploaded)
            st.success("Arquivo carregado! O sistema vai reiniciar.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler upload: {e}")

# SE TUDO ESTIVER OK
if df is not None:
    # Limpeza Técnica (Remove espaços nos nomes das colunas)
    df.columns = df.columns.str.strip()
    
    # Identifica coluna de Assunto/Categoria
    col_cat = next((c for c in df.columns if any(x in c.lower() for x in ['cat', 'assunto', 'area', 'genero'])), None)

    # --- CABEÇALHO ---
    st.markdown("""
        <div style="text-align: left; margin-bottom: 25px;">
            <h1 style='color: #000; font-size: 2.2rem; margin: 0; font-weight: 800;'>Acervo Cinema & Artes</h1>
            <p style='color: #666; font-size: 1.1rem; margin-top: 5px;'>Sistema Integrado de Referência</p>
        </div>
    """, unsafe_allow_html=True)

    # --- MENU UNIFICADO ---
    modo = st.radio("Menu", ["🔍 Pesquisa", "🤖 Consultor IA"], horizontal=True, label_visibility="collapsed")

    # --- ABA 1: PESQUISA ---
    if modo == "🔍 Pesquisa":
        
        # Filtros (Design Limpo)
        cats_sel = []
        if col_cat:
            st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #555; margin-bottom: 2px; text-transform: uppercase;'>Filtrar por Categoria</p>", unsafe_allow_html=True)
            try:
                opcoes = sorted(df[col_cat].dropna().astype(str).unique())
                cats_sel = st.multiselect("Cats", opcoes, label_visibility="collapsed", placeholder="Todas as categorias")
            except:
                pass # Ignora erro se dados estiverem sujos
        
        st.write("") # Espaço
        
        st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #555; margin-bottom: 2px; text-transform: uppercase;'>Busca Textual</p>", unsafe_allow_html=True)
        busca = st.text_input("Busca", placeholder="Digite título, autor ou termo...", label_visibility="collapsed")
        
        if st.button("LOCALIZAR OBRA"):
            res = df.copy()
            
            # Filtra Categoria
            if cats_sel and col_cat:
                res = res[res[col_cat].astype(str).isin(cats_sel)]
            
            # Filtra Texto (Busca Inteligente em todas as colunas)
            if busca:
                mask = res.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)
                res = res[mask]
            
            if not res.empty:
                st.success(f"Encontramos {len(res)} obras.")
                # Mostra tabela bonita, escondendo o índice numérico feio da esquerda
                st.dataframe(res, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhum resultado encontrado para sua busca.")

    # --- ABA 2: IA ---
    elif modo == "🤖 Consultor IA":
        if not api_status:
            st.error("⚠️ ERRO DE SEGURANÇA: API Key não encontrada no arquivo secrets.toml.")
            st.info("Para usar a IA, adicione sua nova chave no arquivo '.streamlit/secrets.toml'.")
        else:
            st.info("💡 **Consultor sVAI:** Pergunte sobre o conteúdo dos livros ou peça recomendações.")
            
            st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #555; margin-bottom: 2px; text-transform: uppercase;'>Sua Pergunta</p>", unsafe_allow_html=True)
            pergunta = st.text_input("Pergunta", placeholder="Ex: Quais autores discutem a montagem no cinema russo?", label_visibility="collapsed")
            
            if st.button("ANALISAR COM IA"):
                if not pergunta:
                    st.warning("Por favor, digite uma pergunta.")
                else:
                    with st.spinner('Lendo o acervo e formulando resposta...'):
                        try:
                            # Contexto: Pega os primeiros 60 livros para a IA ter base
                            txt_acervo = df.head(60).to_string(index=False)
                            
                            prompt = f"""
                            Atue como um Bibliotecário Sênior Especialista.
                            Responda à pergunta: "{pergunta}"
                            
                            Use esta amostra do acervo local como referência principal:
                            ---
                            {txt_acervo}
                            ---
                            
                            Se a resposta não estiver explícita no acervo, use seu conhecimento acadêmico para complementar, mas deixe claro o que é do acervo e o que é externo.
                            """
                            
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            resp = model.generate_content(prompt)
                            
                            st.markdown("### 🤖 Resposta:")
                            st.markdown(resp.text)
                        except Exception as e:
                            st.error(f"Erro na conexão com IA: {e}")
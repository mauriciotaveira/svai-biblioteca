import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO DA PÁGINA (Layout Wide)
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# 2. CONFIGURAÇÃO DA API (COM FALLBACK VISUAL)
# Tenta pegar dos segredos. Se falhar, pede na barra lateral.
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_AIzaSyDAjy4lMSEMjorxG25p08_mxOhQGmPw5uEAPI_KEY"]
    api_status = "✅ Chave Oculta Detectada"
else:
    api_status = "⚠️ Chave não encontrada no arquivo"

# Se não achou no arquivo, cria um campo na barra lateral
if not api_key:
    with st.sidebar:
        st.header("Configuração")
        api_key = st.text_input("CAIzaSyDAjy4lMSEMjorxG25p08_mxOhQGmPw5uE:", type="password")
        if api_key:
            api_status = "✅ Chave Inserida Manualmente"

# Configura a IA se tiver chave
if api_key:
    genai.configure(api_key=api_key)

# 3. MOTOR DE DADOS COM CORREÇÃO BRASILEIRA
@st.cache_data
def carregar_dados_blindado():
    # Procura arquivos na pasta
    arquivos = [f for f in os.listdir() if f.endswith(('.csv', '.xlsx'))]
    
    if not arquivos:
        return None, "Nenhum arquivo encontrado."
    
    arquivo = arquivos[0] # Pega o primeiro que achar
    df = None
    
    try:
        if arquivo.endswith('.csv'):
            # TENTATIVA 1: Padrão Brasileiro (Ponto e vírgula + Latin1)
            # Isso resolve o problema dos acentos estranhos e colunas grudadas
            df = pd.read_csv(arquivo, sep=';', encoding='latin1')
            
            # Se a leitura ficou ruim (só 1 coluna), tenta vírgula e UTF-8
            if df.shape[1] < 2:
                df = pd.read_csv(arquivo, sep=',', encoding='utf-8')
                
        else:
            # Excel direto (.xlsx) é mais seguro, não tem problema de encoding
            df = pd.read_excel(arquivo)
            
        return df, arquivo
    except Exception as e:
        return None, str(e)

# Carrega
df, nome_arquivo = carregar_dados_blindado()

# 4. ESTILO VISUAL (CORRIGIDO PARA LEGIBILIDADE)
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1A1A1A; font-family: 'Inter', sans-serif; }
    
    /* INPUTS ESCUROS (Preto no Branco) */
    input[type="text"], textarea, .stMultiSelect div {
        color: #000000 !important;
        background-color: #FAFAFA !important; 
        border: 1px solid #ced4da !important;
    }
    
    /* BOTÕES PRETOS */
    div.stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 6px;
        height: 50px;
        font-weight: 700;
        width: 100%;
        text-transform: uppercase;
        margin-top: 10px;
    }
    div.stButton > button:hover { background-color: #333 !important; color: #fff !important; }
    
    /* MENUS */
    div[role="radiogroup"] {
        background-color: #F8F9FA;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #ddd;
        display: flex;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# 5. INTERFACE DO USUÁRIO

# Se deu erro no carregamento
if df is None:
    st.error(f"❌ Erro ao ler arquivos: {nome_arquivo}")
    st.info("O sistema tentou ler com separador ';' e ',' mas falhou. Tente subir o arquivo manualmente:")
    uploaded = st.file_uploader("Upload Manual (.xlsx é mais seguro)", type=['xlsx', 'csv'])
    if uploaded:
        try:
            if uploaded.name.endswith('.csv'):
                df = pd.read_csv(uploaded, sep=';', encoding='latin1')
            else:
                df = pd.read_excel(uploaded)
            st.success("Arquivo carregado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro no upload: {e}")

# SE TUDO DEU CERTO
if df is not None:
    # Limpeza de nomes de colunas (remove espaços extras)
    df.columns = df.columns.str.strip()
    
    # Tenta achar a coluna de Categoria automaticamente
    col_cat = next((c for c in df.columns if any(x in c.lower() for x in ['cat', 'assunto', 'area'])), None)
    
    # Cabeçalho
    st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <h1 style='color: #000; margin:0;'>Acervo Cinema & Artes</h1>
            <p style='color: #666;'>Base conectada: <b>{nome_arquivo if isinstance(nome_arquivo, str) else 'Upload Manual'}</b> ({len(df)} itens)</p>
        </div>
    """, unsafe_allow_html=True)

    # Navegação
    modo = st.radio("Menu", ["🔍 Pesquisa", "🤖 Consultor IA"], horizontal=True, label_visibility="collapsed")

    # --- ABA PESQUISA ---
    if modo == "🔍 Pesquisa":
        
        # Filtro de Categoria (Se achou a coluna)
        cats_sel = []
        if col_cat:
            st.caption("FILTRAR POR CATEGORIA")
            try:
                opcoes = sorted(df[col_cat].dropna().astype(str).unique())
                cats_sel = st.multiselect("Cats", options=opcoes, label_visibility="collapsed")
            except:
                st.warning("Dados de categoria inconsistentes.")
        
        st.write("")
        st.caption("TERMO DE BUSCA")
        busca = st.text_input("Busca", placeholder="Digite para buscar...", label_visibility="collapsed")
        
        if st.button("LOCALIZAR"):
            res = df.copy()
            
            # Filtra Categoria
            if cats_sel and col_cat:
                res = res[res[col_cat].astype(str).isin(cats_sel)]
            
            # Filtra Texto (Case Insensitive e trata valores nulos)
            if busca:
                mask = res.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)
                res = res[mask]
            
            if not res.empty:
                st.success(f"{len(res)} itens encontrados.")
                st.dataframe(res, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhum resultado encontrado.")

    # --- ABA IA ---
    elif modo == "🤖 Consultor IA":
        st.info("💡 Pergunte ao especialista (Bibliotecário IA)")
        
        st.caption("SUA PERGUNTA")
        pergunta = st.text_input("Pergunta", placeholder="Ex: Livros sobre Cinema Novo...", label_visibility="collapsed")
        
        if st.button("ANALISAR"):
            if not api_key:
                st.error("❌ ERRO: Cole sua API Key na barra lateral (esquerda)!")
            elif not pergunta:
                st.warning("Digite uma pergunta.")
            else:
                with st.spinner('Lendo acervo...'):
                    try:
                        # Pega uma amostra de texto para a IA
                        txt_acervo = df.head(60).to_string(index=False)
                        
                        prompt = f"""
                        Atue como um Bibliotecário Sênior. Responda à pergunta: "{pergunta}"
                        Baseie-se neste catálogo (mas use seu conhecimento externo se necessário):
                        ---
                        {txt_acervo}
                        ---
                        Responda em Português, de forma culta e formatada.
                        """
                        
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        resp = model.generate_content(prompt)
                        st.markdown("### 🤖 Resposta:")
                        st.markdown(resp.text)
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
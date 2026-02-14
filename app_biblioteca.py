import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# 2. CONFIGURAÇÃO DA API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    api_status = "✅ Conectado"
else:
    api_status = "⚠️ Sem Chave"

# 3. MOTOR DE DADOS BLINDADO (CORREÇÃO DO ERRO PARSER)
@st.cache_data
def carregar_dados_inteligente():
    # Pega todos os arquivos da pasta atual
    arquivos_na_pasta = os.listdir()
    
    # Procura QUALQUER arquivo que termine com .csv ou .xlsx
    arquivos_csv = [f for f in arquivos_na_pasta if f.endswith('.csv')]
    arquivos_excel = [f for f in arquivos_na_pasta if f.endswith('.xlsx')]
    
    # --- TENTATIVA DE LEITURA ROBUSTA ---
    if arquivos_csv:
        arquivo = arquivos_csv[0]
        print(f"Tentando ler CSV: {arquivo}")
        
        try:
            # Tentativa 1: Padrão (Vírgula e UTF-8)
            return pd.read_csv(arquivo)
        except:
            try:
                # Tentativa 2: Padrão Brasileiro (Ponto e Vírgula e Latin1) - O MAIS PROVÁVEL
                return pd.read_csv(arquivo, sep=';', encoding='latin1')
            except:
                try:
                    # Tentativa 3: Força bruta (Ignora linhas ruins e tenta adivinhar separador)
                    return pd.read_csv(arquivo, sep=None, engine='python', on_bad_lines='skip')
                except Exception as e:
                    st.error(f"Não consegui ler o CSV '{arquivo}'. Erro: {e}")
                    return None
    
    elif arquivos_excel:
        return pd.read_excel(arquivos_excel[0])
    
    return None

# Carrega os dados automaticamente com a nova proteção
df = carregar_dados_inteligente()

# 4. ESTILO VISUAL
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1A1A1A; font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1.5rem !important; }
    [data-testid="stToolbar"], footer {visibility: hidden;}

    /* INPUTS */
    input[type="text"], textarea, .stMultiSelect div {
        color: #000000 !important;
        background-color: #FAFAFA !important; 
        border: 1px solid #ced4da !important;
    }
    
    /* BOTÕES */
    div.stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        height: 50px !important;
        font-weight: 700 !important;
        width: 100%;
        text-transform: uppercase;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
    }

    /* MENU */
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
        color: #333 !important; font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# 5. INTERFACE

# Se ainda assim falhar (arquivo muito corrompido), oferece upload
if df is None:
    st.error("❌ Erro de leitura: O arquivo CSV existe, mas o formato está confuso para o sistema.")
    st.info("Dica: Abra seu Excel, vá em 'Salvar Como' e escolha 'CSV UTF-8 (Delimitado por vírgulas)'.")
    uploaded = st.file_uploader("Ou tente subir o arquivo novamente aqui:", type=['csv', 'xlsx'])
    if uploaded:
        try:
            if uploaded.name.endswith('.csv'):
                # Tenta ler o upload com a mesma lógica robusta
                try:
                    df = pd.read_csv(uploaded)
                except:
                    uploaded.seek(0)
                    df = pd.read_csv(uploaded, sep=';', encoding='latin1')
            else:
                df = pd.read_excel(uploaded)
            st.rerun()
        except Exception as e:
            st.error(f"Ainda deu erro: {e}")

# Se os dados foram carregados
if df is not None:
    df.columns = df.columns.str.strip()
    
    col_categoria = None
    for c in df.columns:
        if any(x in c.lower() for x in ['cat', 'assunto', 'area', 'genero']):
            col_categoria = c
            break

    st.markdown("""
        <div style="text-align: left; margin-bottom: 20px;">
            <h1 style='font-size: 2.2rem; color: #000; margin: 0;'>Acervo Cinema & Artes</h1>
            <p style='color: #666; margin-top: 5px;'>Sistema Integrado de Pesquisa</p>
        </div>
    """, unsafe_allow_html=True)

    modo = st.radio("Menu", ["🔍 Pesquisa", "🤖 Consultor IA"], horizontal=True, label_visibility="collapsed")

    # --- MODO PESQUISA ---
    if modo == "🔍 Pesquisa":
        filtro_cats = []
        if col_categoria:
            st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #333; margin-bottom: 0;'>CATEGORIAS</p>", unsafe_allow_html=True)
            try:
                opcoes = sorted(df[col_categoria].dropna().astype(str).unique())
                filtro_cats = st.multiselect("Cats", options=opcoes, label_visibility="collapsed", placeholder="Selecione temas...")
            except:
                st.warning("Não foi possível listar categorias (dados inconsistentes na coluna).")
            st.write("") 

        st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #333; margin-bottom: 0;'>TERMO</p>", unsafe_allow_html=True)
        termo = st.text_input("Busca", placeholder="Título, autor...", label_visibility="collapsed")
        
        if st.button("LOCALIZAR"):
            res = df.copy()
            if filtro_cats and col_categoria:
                res = res[res[col_categoria].astype(str).isin(filtro_cats)]
            if termo:
                mask = res.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
                res = res[mask]
            
            if not res.empty:
                st.success(f"{len(res)} itens encontrados.")
                st.dataframe(res, use_container_width=True, hide_index=True)
            else:
                st.warning("Nada encontrado.")

    # --- MODO IA ---
    elif modo == "🤖 Consultor IA":
        st.info("💡 Pergunte ao especialista.")
        st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #333; margin-bottom: 0;'>SUA DÚVIDA</p>", unsafe_allow_html=True)
        pergunta = st.text_input("Dúvida", placeholder="Ex: Livros sobre Nouvelle Vague...", label_visibility="collapsed")
        
        if st.button("ANALISAR"):
            if api_status == "⚠️ Sem Chave":
                st.error("Erro: API Key não encontrada no secrets.toml")
            elif not pergunta:
                st.warning("Digite uma pergunta.")
            else:
                with st.spinner('Lendo acervo...'):
                    try:
                        txt_acervo = df.head(60).to_string(index=False)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        resp = model.generate_content(f"Seja um bibliotecário. Responda: '{pergunta}'. Baseie-se neste acervo: \n\n{txt_acervo}")
                        st.markdown("### 🤖 Resposta:")
                        st.markdown(resp.text)
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
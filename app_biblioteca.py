import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO DA PÁGINA (Layout Wide + Sidebar Escondida)
st.set_page_config(
    page_title="Acervo Cinema & Artes", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. SEGURANÇA DA API
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    if api_key:
        genai.configure(api_key=api_key)
        api_status = True
else:
    api_status = False 

# 3. FUNÇÃO DE LEITURA "MULTIPLEX" (Tenta de tudo para ler o arquivo)
@st.cache_data
def carregar_arquivo_final(file_buffer):
    # Se for Excel (.xlsx), é direto e seguro
    if file_buffer.name.endswith('.xlsx'):
        try:
            return pd.read_excel(file_buffer)
        except Exception as e:
            st.error(f"Erro ao ler Excel: {e}")
            return None

    # Se for CSV, vamos tentar as 3 combinações mais comuns
    if file_buffer.name.endswith('.csv'):
        
        # TENTATIVA 1: Padrão Brasileiro (O mais provável)
        try:
            file_buffer.seek(0) # Rebobina para o início
            return pd.read_csv(file_buffer, sep=';', encoding='latin1', on_bad_lines='skip')
        except:
            pass # Se falhar, tenta o próximo silenciosamente

        # TENTATIVA 2: Padrão Internacional (Vírgula e UTF-8)
        try:
            file_buffer.seek(0) # Rebobina
            return pd.read_csv(file_buffer, sep=',', encoding='utf-8', on_bad_lines='skip')
        except:
            pass

        # TENTATIVA 3: Motor Python (Mais lento, mas "adivinha" o separador)
        try:
            file_buffer.seek(0) # Rebobina
            return pd.read_csv(file_buffer, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        except:
            return None # Desiste se nada funcionar

    return None

# 4. DESIGN CSS (Visual Limpo)
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1A1A1A; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { display: none; } /* Esconde Sidebar */
    section[data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; max-width: 100% !important; }
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
        border: none; border-radius: 6px; height: 50px;
        font-weight: 700; width: 100%; text-transform: uppercase; margin-top: 15px;
    }
    div.stButton > button:hover { background-color: #333 !important; }

    /* MENU */
    div[role="radiogroup"] {
        background-color: #F1F3F5; padding: 8px; border-radius: 8px;
        border: 1px solid #E9ECEF; display: flex; justify-content: center; margin-bottom: 30px;
    }
    div[role="radiogroup"] label { color: #333 !important; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# 5. LÓGICA DE ARQUIVOS AUTOMÁTICA
df = None
# Tenta achar arquivos na pasta automaticamente
arquivos_pasta = [f for f in os.listdir() if f.endswith(('.csv', '.xlsx'))]
if arquivos_pasta:
    try:
        arquivo_local = arquivos_pasta[0]
        if arquivo_local.endswith('.csv'):
            # Tenta ler o arquivo local com ponto e vírgula primeiro
            try:
                df = pd.read_csv(arquivo_local, sep=';', encoding='latin1', on_bad_lines='skip')
            except:
                df = pd.read_csv(arquivo_local, sep=',', encoding='utf-8', on_bad_lines='skip')
        else:
            df = pd.read_excel(arquivo_local)
    except:
        pass # Se falhar o automático, vai pedir upload manual

# 6. INTERFACE

# CABEÇALHO
st.markdown("""
    <div style="text-align: left; margin-bottom: 25px;">
        <h1 style='color: #000; font-size: 2.2rem; margin: 0; font-weight: 800;'>Acervo Cinema & Artes</h1>
        <p style='color: #666; font-size: 1.1rem; margin-top: 5px;'>Sistema Integrado de Referência</p>
    </div>
""", unsafe_allow_html=True)

# SE NÃO CARREGOU AUTOMÁTICO, PEDE UPLOAD
if df is None:
    st.info("📂 Arraste seu arquivo (CSV ou Excel) abaixo.")
    uploaded = st.file_uploader("Upload", type=['csv', 'xlsx'])
    
    if uploaded:
        df = carregar_arquivo_final(uploaded)
        if df is not None:
            st.success("Arquivo lido com sucesso! O sistema vai reiniciar.")
            st.rerun()
        else:
            st.error("❌ Não foi possível ler o arquivo. Dica: Salve seu Excel como '.xlsx' em vez de CSV, é mais seguro.")

# SE TUDO OK, MOSTRA O SISTEMA
if df is not None:
    df.columns = df.columns.str.strip()
    col_cat = next((c for c in df.columns if any(x in c.lower() for x in ['cat', 'assunto', 'area', 'genero'])), None)

    # MENU
    modo = st.radio("Menu", ["🔍 Pesquisa", "🤖 Consultor IA"], horizontal=True, label_visibility="collapsed")

    # --- PESQUISA ---
    if modo == "🔍 Pesquisa":
        cats_sel = []
        if col_cat:
            st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #555; margin: 0;'>CATEGORIA</p>", unsafe_allow_html=True)
            try:
                opcoes = sorted(df[col_cat].dropna().astype(str).unique())
                cats_sel = st.multiselect("Cats", opcoes, label_visibility="collapsed")
            except: pass
        
        st.write("") 
        st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #555; margin: 0;'>BUSCA</p>", unsafe_allow_html=True)
        busca = st.text_input("Busca", placeholder="Título, autor...", label_visibility="collapsed")
        
        if st.button("LOCALIZAR OBRA"):
            res = df.copy()
            if cats_sel and col_cat:
                res = res[res[col_cat].astype(str).isin(cats_sel)]
            if busca:
                mask = res.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)
                res = res[mask]
            
            if not res.empty:
                st.success(f"Encontramos {len(res)} obras.")
                st.dataframe(res, use_container_width=True, hide_index=True)
            else:
                st.warning("Nada encontrado.")

    # --- IA ---
    elif modo == "🤖 Consultor IA":
        if not api_status:
            st.error("🔒 Configure a API Key no arquivo secrets.toml.")
        else:
            st.info("💡 Pergunte ao Consultor sVAI.")
            st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #555; margin: 0;'>PERGUNTA</p>", unsafe_allow_html=True)
            pergunta = st.text_input("Pergunta", placeholder="Ex: Livros sobre Cinema Novo...", label_visibility="collapsed")
            
            if st.button("ANALISAR"):
                if not pergunta:
                    st.warning("Digite uma pergunta.")
                else:
                    with st.spinner('Analisando...'):
                        try:
                            txt_acervo = df.head(60).to_string(index=False)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            resp = model.generate_content(f"Responda: '{pergunta}'. Base: \n{txt_acervo}")
                            st.markdown("### 🤖 Resposta:")
                            st.markdown(resp.text)
                        except Exception as e:
                            st.error(f"Erro IA: {e}")
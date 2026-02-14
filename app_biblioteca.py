import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO INSTITUCIONAL
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Acervo Cinema & Artes", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. SEGURANÇA E CONEXÃO (BACKEND)
# -----------------------------------------------------------------------------
api_status = False

try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        api_status = True
except Exception as e:
    # Em produção, não mostramos o erro técnico, apenas registramos
    api_status = False

# -----------------------------------------------------------------------------
# 3. MOTOR DE DADOS (LEITURA BRASILEIRA NATIVA)
# -----------------------------------------------------------------------------
@st.cache_data
def carregar_dados_blindado(file_buffer=None):
    """
    Tenta ler arquivos CSV/Excel lidando com as peculiaridades
    de codificação do Excel Brasileiro (Latin1 e Ponto e Vírgula).
    """
    # Se não foi passado arquivo, tenta achar na pasta (Deploy automático)
    if file_buffer is None:
        arquivos = [f for f in os.listdir() if f.endswith(('.csv', '.xlsx'))]
        if not arquivos: return None
        file_path = arquivos[0]
        
        # Leitura de Arquivo Local
        try:
            if file_path.endswith('.xlsx'):
                return pd.read_excel(file_path)
            else:
                # Tenta padrão BR primeiro
                return pd.read_csv(file_path, sep=';', encoding='latin1', on_bad_lines='skip')
        except:
            try:
                # Fallback para padrão US
                return pd.read_csv(file_path, sep=',', encoding='utf-8', on_bad_lines='skip')
            except:
                return None

    # Se foi passado um arquivo via Upload (Pelo usuário)
    else:
        try:
            if file_buffer.name.endswith('.xlsx'):
                return pd.read_excel(file_buffer)
            else:
                # O segredo do sucesso: Rebobinar e tentar Latin1
                file_buffer.seek(0)
                return pd.read_csv(file_buffer, sep=';', encoding='latin1', on_bad_lines='skip')
        except:
            try:
                file_buffer.seek(0)
                return pd.read_csv(file_buffer, sep=',', encoding='utf-8', on_bad_lines='skip')
            except:
                return None
    return None

# Tenta carga automática
df = carregar_dados_blindado()

# -----------------------------------------------------------------------------
# 4. DESIGN SYSTEM (INTERFACE VISUAL)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    /* RESET GERAL */
    .stApp { background-color: #FFFFFF; color: #1A1A1A; font-family: 'Inter', sans-serif; }
    
    /* LAYOUT FULL SCREEN (Sem Sidebar) */
    [data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 2rem !important; max-width: 100% !important; }
    [data-testid="stToolbar"], footer { visibility: hidden; }

    /* COMPONENTES DE UI */
    input[type="text"], textarea, .stMultiSelect div {
        color: #000000 !important;
        background-color: #F8F9FA !important; 
        border: 1px solid #DEE2E6 !important;
    }
    
    /* BOTÕES PRIMÁRIOS */
    div.stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none; border-radius: 6px; height: 50px;
        font-weight: 700; width: 100%; text-transform: uppercase; margin-top: 15px;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover { 
        background-color: #333333 !important; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* MENU DE NAVEGAÇÃO */
    div[role="radiogroup"] {
        background-color: #F1F3F5; padding: 8px; border-radius: 8px;
        display: flex; justify-content: center; margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. FRONTEND (APLICAÇÃO)
# -----------------------------------------------------------------------------

# Cabeçalho Institucional
st.markdown("""
    <div style="margin-bottom: 25px;">
        <h1 style='color: #000; font-size: 2.2rem; margin: 0; font-weight: 800;'>Acervo Cinema & Artes</h1>
        <p style='color: #666; font-size: 1.1rem; margin-top: 5px;'>Sistema Integrado de Referência</p>
    </div>
""", unsafe_allow_html=True)

# Tela de Carga (Se não houver dados)
if df is None:
    st.info("📂 Base de dados não detectada. Por favor, carregue o arquivo mestre.")
    uploaded = st.file_uploader("Carregar Acervo (.xlsx ou .csv)", type=['csv', 'xlsx'])
    if uploaded:
        df = carregar_dados_blindado(uploaded)
        if df is not None:
            st.success("Acervo indexado com sucesso.")
            st.rerun()
        else:
            st.error("Erro crítico: Formato de arquivo incompatível.")

# Aplicação Principal
if df is not None:
    # Sanitização de Colunas
    df.columns = df.columns.str.strip()
    col_cat = next((c for c in df.columns if any(x in c.lower() for x in ['cat', 'assunto', 'area', 'genero'])), None)

    # Navegação
    modo = st.radio("Módulo", ["🔍 Pesquisa no Acervo", "🤖 Consultor IA"], horizontal=True, label_visibility="collapsed")

    # --- MÓDULO PESQUISA ---
    if modo == "🔍 Pesquisa no Acervo":
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#555; margin-bottom:5px;'>FILTRAR CATEGORIA</p>", unsafe_allow_html=True)
            cats_sel = []
            if col_cat:
                try:
                    opcoes = sorted(df[col_cat].dropna().astype(str).unique())
                    cats_sel = st.multiselect("Filtro", opcoes, label_visibility="collapsed")
                except: pass

        with col2:
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#555; margin-bottom:5px;'>BUSCA TEXTUAL</p>", unsafe_allow_html=True)
            busca = st.text_input("Busca", placeholder="Título, autor, ano...", label_visibility="collapsed")
        
        if st.button("LOCALIZAR REGISTROS"):
            res = df.copy()
            if cats_sel and col_cat:
                res = res[res[col_cat].astype(str).isin(cats_sel)]
            if busca:
                mask = res.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)
                res = res[mask]
            
            if not res.empty:
                st.success(f"{len(res)} obras encontradas.")
                st.dataframe(res, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhum registro encontrado para os critérios informados.")

    # --- MÓDULO CONSULTOR IA ---
    elif modo == "🤖 Consultor IA":
        if not api_status:
            st.error("🔒 **Serviço Indisponível:** A chave de API não foi configurada no servidor.")
            st.info("Entre em contato com o administrador do sistema para configurar os 'Secrets'.")
        else:
            st.info("💡 **Consultor sVAI:** Especialista virtual em Cinema e Artes.")
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#555; margin-bottom:5px;'>PERGUNTA DE REFERÊNCIA</p>", unsafe_allow_html=True)
            pergunta = st.text_input("Pergunta", placeholder="Ex: Quais são os principais teóricos da montagem russa?", label_visibility="collapsed")
            
            if st.button("ANALISAR COM IA"):
                if not pergunta:
                    st.warning("Por favor, insira uma pergunta.")
                else:
                    with st.spinner('Processando consulta...'):
                        try:
                            # Contexto Otimizado (Segurança de Tokens)
                            txt_acervo = df.head(60).to_string(index=False)
                            
                            prompt = f"""
                            Atue como um Bibliotecário Acadêmico Sênior.
                            Pergunta do usuário: "{pergunta}"
                            
                            Base de dados local (amostra):
                            ---
                            {txt_acervo}
                            ---
                            
                            Instruções:
                            1. Responda em Português formal e acadêmico.
                            2. Priorize obras que constam na base de dados acima.
                            3. Se necessário, complemente com conhecimento externo clássico.
                            """
                            
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            resp = model.generate_content(prompt)
                            
                            st.markdown("### 🤖 Parecer do Consultor:")
                            st.markdown(resp.text)
                        except Exception as e:
                            st.error("Erro de comunicação com o serviço de IA. Tente novamente.")
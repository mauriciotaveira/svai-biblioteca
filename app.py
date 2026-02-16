import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re
import unicodedata

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA", page_icon="🎬", layout="wide")

# --- 2. CSS AGRESSIVO (SOLUÇÃO FINAL) ---
st.markdown("""
<style>
    /* GARANTIA DE FUNDO BRANCO */
    .stApp {
        background-color: #ffffff !important;
    }

    /* 1. CORREÇÃO DO BOTÃO (PRETO SÓLIDO) */
    /* Alvo em todos os tipos de botões do Streamlit */
    div.stButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important; /* Força Branco no Mobile */
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
        border-color: #333333 !important;
    }
    div.stButton > button:active {
        background-color: #000000 !important;
        color: #ffffff !important;
    }

    /* 2. CORREÇÃO DA SUGESTÃO (PLACEHOLDER) */
    /* O segredo para Mobile: -webkit-text-fill-color */
    ::placeholder {
        color: #666666 !important;
        -webkit-text-fill-color: #666666 !important; /* Essencial para Android/iOS */
        opacity: 1 !important;
        font-style: italic;
    }
    
    /* Input de Texto */
    input.st-ai, input.st-ah, div[data-baseweb="input"] input {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; /* Texto digitado PRETO */
        caret-color: #000000 !important; /* Cursor piscando PRETO */
    }

    /* 3. DESIGN GERAL */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Exceções visuais */
    .titulo-tech {
        font-family: 'Helvetica', sans-serif; 
        font-size: 3.5rem; font-weight: 900; line-height: 1.0; 
        letter-spacing: -1px; margin-bottom: 5px;
    }
    .subtitulo-tech {
        font-family: 'Helvetica', sans-serif; color: #444 !important; -webkit-text-fill-color: #444 !important;
        font-size: 1.2rem; margin-bottom: 25px;
    }
    .box-instrucao {
        background-color: #f0f7ff !important; padding: 15px; border-radius: 8px;
        border-left: 6px solid #0066cc; color: #333 !important; -webkit-text-fill-color: #333 !important;
        font-size: 1rem; margin-bottom: 30px;
    }
    .destaque-tech { font-weight: bold; color: #0066cc !important; -webkit-text-fill-color: #0066cc !important; }
    
    .book-card {
        background: white !important; padding: 15px; border-radius: 12px;
        border: 1px solid #e0e0e0; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .ai-card {
        background-color: #f8f9fa !important; border-left: 5px solid #333; 
        padding: 15px; border-radius: 5px; margin-top: 15px; 
    }
    .tag { background: #eee !important; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; color: #555 !important; -webkit-text-fill-color: #555 !important; text-transform: uppercase;}
    
    /* Ajuste responsivo */
    @media (max-width: 768px) { 
        .titulo-tech { font-size: 2.5rem !important; } 
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CONEXÃO ---
api_key = st.secrets.get("GOOGLE_API_KEY")

# --- 4. DADOS ---
def normalizar_texto(texto):
    if not isinstance(texto, str): return str(texto).lower()
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

@st.cache_data
def carregar_dados():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not arquivos: return None
    try:
        df_bruto = pd.read_excel(arquivos[0], header=None)
        inicio = 0
        for i, row in df_bruto.head(15).iterrows():
            if any(x in str(row.values).lower() for x in ['título', 'autor']):
                inicio = i; break
        df = pd.read_excel(arquivos[0], header=inicio)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')].dropna(how='all').fillna('').astype(str)
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        if col_cat: df[col_cat] = df[col_cat].apply(lambda x: re.sub(r'\+.*', '', str(x)).strip())
        return df
    except: return None

df = carregar_dados()

# --- 5. INTERFACE ---
st.markdown('<div class="titulo-tech">Cine.IA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo-tech">Inteligência para Criar Filmes</div>', unsafe_allow_html=True)

st.markdown('''
<div class="box-instrucao">
    🤖 <b>Seu Assistente de Produção</b><br>
    Pergunte: "Como <span class="destaque-tech">financiar um curta</span>?", 
    "Regra dos <span class="destaque-tech">180 graus</span>" ou 
    "Dicas de <span class="destaque-tech">iluminação</span>".
</div>
''', unsafe_allow_html=True)

if df is not None:
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuração")
        modelo_escolhido = None
        if api_key:
            try:
                genai.configure(api_key=api_key)
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                nomes_limpos = [m.replace('models/', '') for m in modelos]
                st.success("✅ Online")
                modelo_escolhido = st.selectbox("Motor IA:", nomes_limpos, index=0)
            except: st.error("Erro Conexão")
        
        st.divider()
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Filtrar Área:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st.metric("Obras", len(df))
        st.divider()
        st.link_button("🔗 Abrir App", "https://svai-biblioteca-ia.streamlit.app/")

    df_base = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    tab1, tab2 = st.tabs(["🎬 Chat Assistente", "📚 Buscar Livros"])

    # --- ABA 1 ---
    with tab1:
        # Texto de ajuda fixo (caso o placeholder falhe)
        st.markdown("<small style='color:#666; font-style:italic;'>Ex: 'Como criar suspense?' ou 'Técnicas de roteiro'</small>", unsafe_allow_html=True)
        
        # Input corrigido
        pgt = st.text_input("Dúvida", placeholder="Digite sua dúvida aqui...", label_visibility="collapsed")
        
        if st.button("Pedir Orientação"):
            if modelo_escolhido and api_key:
                try:
                    ctx = df_base.head(60).to_string(index=False)
                    model = genai.GenerativeModel(modelo_escolhido)
                    prompt = f"""Atue como Especialista em Cinema. Base: {ctx}. Pergunta: {pgt}.
                    Dê dicas práticas e cite livros do acervo."""
                    
                    with st.spinner("Analisando..."):
                        response = model.generate_content(prompt)
                        st.markdown(f"""<div class="ai-card"><b>🤖 Resposta:</b><br>{response.text}</div>""", unsafe_allow_html=True)
                except Exception as e: st.error(f"Erro: {e}")
            else: st.error("Erro API")

    # --- ABA 2 ---
    with tab2:
        st.markdown("<small style='color:#666; font-style:italic;'>Ex: 'montagem', 'iluminação', 'som'</small>", unsafe_allow_html=True)
        termo = st.text_input("Busca", placeholder="Digite um termo...", label_visibility="collapsed")
        
        if st.button("Buscar"):
            if termo:
                termo_limpo = normalizar_texto(termo)
                ignorar = ['livro', 'sobre', 'de', 'do', 'que', 'tem', 'quero']
                pals = [p for p in termo_limpo.split() if len(p) > 2 and p not in ignorar]
                
                if pals:
                    mask = df_base.apply(lambda r: all(p in normalizar_texto(str(r.values)) for p in pals), axis=1)
                    res = df_base[mask]
                    if not res.empty:
                        for _, row in res.iterrows():
                            c_tit = df.columns[0]
                            st.markdown(f"""<div class="book-card">
                                <b>{row.iloc[0]}</b><br>
                                <small style="color:#0066cc">{row.iloc[1]}</small><br>
                                <span style="font-size:13px">{row.iloc[4]}</span>
                            </div>""", unsafe_allow_html=True)
                    else: st.info("Nada encontrado.")
                else: st.warning("Digite um termo mais específico.")

else: st.error("Excel não carregado.")

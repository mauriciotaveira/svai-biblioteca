import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re
import unicodedata

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA", page_icon="🎬", layout="wide")

# --- 2. CSS FINAL (VISUAL PERFEITO) ---
st.markdown("""
<style>
    /* Força fundo branco */
    .stApp { background-color: #ffffff !important; }

    /* --- BOTÃO (FUNDO PRETO, TEXTO BRANCO) --- */
    div.stButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
        color: #ffffff !important;
    }
    div.stButton > button p { color: #ffffff !important; }

    /* --- TEXTOS GERAIS (PRETO) --- */
    h1, h2, h3, h4, h5, h6, .stMarkdown p, .stMarkdown li, label, div {
        color: #000000 !important;
    }

    /* --- INPUTS --- */
    .stTextInput input {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
    }
    ::placeholder { color: #888888 !important; font-style: italic !important; opacity: 1 !important; }

    /* --- DESIGN GERAL --- */
    .titulo-tech {
        font-family: 'Helvetica', sans-serif; 
        color: #000000 !important;
        font-size: 3.5rem; font-weight: 900; margin-bottom: 5px; line-height: 1.0; letter-spacing: -1px;
    }
    .subtitulo-tech {
        font-family: 'Helvetica', sans-serif; color: #444444 !important; font-size: 1.2rem; margin-bottom: 25px;
    }
    .box-instrucao {
        background-color: #f0f7ff !important; padding: 15px; border-radius: 8px;
        border-left: 6px solid #0066cc; color: #333333 !important; font-size: 1rem; margin-bottom: 30px;
    }
    .destaque-tech { font-weight: bold; color: #0066cc !important; }
    
    .book-card {
        background: white !important; padding: 15px; border-radius: 12px;
        border: 1px solid #e0e0e0; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .book-card b, .book-card span { color: #000000 !important; }
    
    .ai-card {
        background-color: #f8f9fa !important; border-left: 5px solid #333; 
        padding: 15px; border-radius: 5px; margin-top: 15px; color: #000000 !important;
    }
    @media (max-width: 768px) { .titulo-tech { font-size: 2.5rem !important; } }
</style>
""", unsafe_allow_html=True)

# --- 3. DADOS E FUNÇÕES ---
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
        # Limpeza pesada para garantir busca
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')].dropna(how='all').fillna('').astype(str)
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        if col_cat: df[col_cat] = df[col_cat].apply(lambda x: re.sub(r'\+.*', '', str(x)).strip())
        return df
    except: return None

df = carregar_dados()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.secrets.get("GOOGLE_API_KEY")
    modelo_escolhido = None
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Lista modelos disponíveis
            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            nomes_limpos = [m.replace('models/', '') for m in modelos]
            st.success("✅ Online")
            modelo_escolhido = st.selectbox("Motor IA:", nomes_limpos, index=0)
        except: st.error("Erro Conexão")
    
    st.divider()
    if df is not None:
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Filtrar Área:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st.metric("Obras", len(df))
        st.divider()
        st.link_button("🔗 Abrir App", "https://svai-biblioteca-ia.streamlit.app/")

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
    df_base = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    tab1, tab2 = st.tabs(["🎬 Assistente de Produção", "📚 Buscar Livros"])

    # --- ABA 1: O CHAT INTELIGENTE (AGORA COM RANKING!) ---
    with tab1:
        st.markdown("<small style='color:#666; font-style:italic;'>Ex: 'Como criar suspense?' ou 'Técnicas de roteiro'</small>", unsafe_allow_html=True)
        pgt = st.text_input("Dúvida", placeholder="Digite sua dúvida aqui...", label_visibility="collapsed")
        
        if st.button("Pedir Orientação"):
            if modelo_escolhido and api_key:
                try:
                    # 1. Normaliza e pega palavras-chave
                    pgt_norm = normalizar_texto(pgt)
                    ignorar = ['como', 'fazer', 'o', 'que', 'e', 'um', 'uma', 'de', 'do', 'da', 'para', 'com', 'livro', 'sobre']
                    palavras = [p for p in pgt_norm.split() if p not in ignorar and len(p) > 2]
                    
                    if not palavras: palavras = pgt_norm.split() # Fallback

                    # 2. Pontua cada linha do Excel
                    def pontuar(row):
                        txt = normalizar_texto(str(row))
                        return sum(1 for p in palavras if p in txt)

                    df_base['score'] = df_base.apply(lambda r: pontuar(r.values), axis=1)
                    
                    # 3. Pega as 20 melhores (As que têm as palavras da busca!)
                    melhores = df_base.sort_values('score', ascending=False).head(20)
                    ctx = melhores.to_string(index=False)
                    
                    # 4. Envia para a IA
                    model = genai.GenerativeModel(modelo_escolhido)
                    
                    # ==============================================================
                    # O NOVO PROMPT (COM REGRAS DE BIBLIOTECONOMIA / ABNT)
                    # ==============================================================
                    prompt = f"""
                    Atue como o Cine.IA, um Especialista em Cinema e Produção, mas operando com o rigor acadêmico de um Bibliotecário Sênior.
                    Você tem acesso a este ACERVO DE LIVROS selecionados (os mais relevantes para a pergunta estão no topo):
                    {ctx}
                    
                    Pergunta do Usuário: {pgt}
                    
                    Instruções:
                    1. Responda a dúvida técnica de forma didática e clara.
                    2. CITE OS LIVROS DO ACERVO que ajudam nesse tema.
                    3. OBRIGATORIAMENTE, crie uma seção no final chamada "REFERÊNCIAS" e liste todas as obras mencionadas usando o rigoroso padrão ABNT (Associação Brasileira de Normas Técnicas).
                    
                    REGRAS RÍGIDAS DE FORMATAÇÃO (BIBLIOTECONOMIA / ABNT):
                    - Para Filmes/Audiovisual: TÍTULO DO FILME (em letras maiúsculas). Direção: Nome do Diretor. Produção: Nome do Produtor ou Estúdio. Local (País): Produtora, Ano de lançamento.
                    - Para Livros: SOBRENOME DO AUTOR (em maiúsculas), Nome do Autor. Título da obra: subtítulo. Número da edição. Local de publicação (Cidade): Editora, Ano. (Se faltarem dados de cidade ou ano no acervo fornecido, utilize as convenções [S.l.] ou [s.d.]).
                    """
                    # ==============================================================

                    with st.spinner("Consultando biblioteca técnica..."):
                        response = model.generate_content(prompt)
                        st.markdown(f"""<div class="ai-card"><b>🤖 Resposta:</b><br>{response.text}</div>""", unsafe_allow_html=True)
                        
                except Exception as e: st.error(f"Erro: {e}")
            else: st.error("Erro API")

    # --- ABA 2: BUSCA MANUAL ---
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
                            vals = row.values
                            # Tenta pegar as colunas certas dinamicamente
                            c_tit = vals[0]
                            c_aut = vals[1] if len(vals) > 1 else ""
                            c_res = vals[4] if len(vals) > 4 else ""
                            
                            # ==========================================
                            # CORREÇÃO AQUI: String segura, sem aspas triplas!
                            # ==========================================
                            html_card = (
                                f'<div class="book-card">'
                                f'<b>{c_tit}</b><br>'
                                f'<small style="color:#0066cc">{c_aut}</small><br>'
                                f'<span style="font-size:13px">{c_res}</span>'
                                f'</div>'
                            )
                            st.markdown(html_card, unsafe_allow_html=True)
                            
                    else: st.info("Nada encontrado.")
                else: st.warning("Digite um termo mais específico.")

else: st.error("Excel não carregado.")

import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re
import unicodedata

# --- 1. CONFIGURAÇÃO VISUAL & CSS ---
st.set_page_config(page_title="Cine.IA | Inteligência Criativa", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    @media (max-width: 768px) { h1 { font-size: 2rem !important; } }
    .block-container { padding-top: 2rem; }
    .main { background-color: #ffffff; color: #000000; }

    /* TÍTULO PRINCIPAL */
    .titulo-tech {
        font-family: 'Helvetica', 'Arial', sans-serif;
        color: #000000;
        font-size: 4rem;       
        font-weight: 900;      
        line-height: 1.0;
        letter-spacing: -1px;
        margin-bottom: 5px;
    }

    /* SUBTÍTULO */
    .subtitulo-tech {
        font-family: 'Helvetica', sans-serif;
        color: #444;
        font-size: 1.5rem;
        font-weight: 400;
        margin-bottom: 25px;
    }

    /* CAIXA DIDÁTICA */
    .box-instrucao {
        background-color: #f0f7ff; 
        padding: 20px;
        border-radius: 8px;
        border-left: 6px solid #0066cc; 
        color: #333;
        font-size: 1.1rem;
        margin-bottom: 30px;
        line-height: 1.6;
    }
    .destaque-tech { font-weight: bold; color: #0066cc; }

    /* Elementos Visuais */
    .book-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e0e0e0; margin-bottom: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .ai-card {
        background-color: #f8f9fa; border-left: 5px solid #333; 
        padding: 20px; border-radius: 5px; margin-top: 15px; color: #333;
    }
    
    /* Botão Principal */
    .stButton>button { 
        background-color: #000; color: white; border-radius: 8px; 
        width: 100%; height: 50px; border: none; font-weight: bold; font-size: 16px;
    }
    .stButton>button:hover { background-color: #333; color: #fff; }
    
    h4 { color: #000; margin-bottom: 5px; font-weight: 800; }
    .tag { background: #eee; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #555; text-transform: uppercase;}
</style>
""", unsafe_allow_html=True)

# --- 2. CONEXÃO ---
api_key = st.secrets.get("GOOGLE_API_KEY")

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
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')].dropna(how='all').fillna('').astype(str)
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        if col_cat: df[col_cat] = df[col_cat].apply(lambda x: re.sub(r'\+.*', '', str(x)).strip())
        return df
    except: return None

df = carregar_dados()

# --- 4. INTERFACE ---
st.markdown('<div class="titulo-tech">Cine.IA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo-tech">Inteligência para Criar Filmes</div>', unsafe_allow_html=True)

st.markdown('''
<div class="box-instrucao">
    🤖 <b>Seu Assistente de Produção</b><br>
    Nossa IA analisa centenas de livros técnicos para resolver seus problemas de filmagem, roteiro e edição.<br>
    <i>Experimente perguntar:</i> "Como <span class="destaque-tech">financiar um curta</span>?", 
    "A regra dos <span class="destaque-tech">180 graus</span>" ou 
    "Dicas de <span class="destaque-tech">iluminação noir</span>".
</div>
''', unsafe_allow_html=True)

if df is not None:
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuração IA")
        modelo_escolhido = None
        if api_key:
            try:
                genai.configure(api_key=api_key)
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                nomes_limpos = [m.replace('models/', '') for m in modelos]
                st.success("✅ Sistema Online")
                modelo_escolhido = st.selectbox("Motor de Inteligência:", nomes_limpos, index=0)
            except: st.error("Erro de Conexão")
        
        st.divider()
        st.header("🗂️ Filtros de Acervo")
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Área de Interesse:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st.metric("Obras Técnicas", len(df))
        
        st.divider()
        st.markdown("### 🌐 Acesso Rápido")
        st.link_button("🔗 Abrir Cine.IA", "https://svai-biblioteca-ia.streamlit.app/")

    df_base = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    # Abas na ordem correta
    tab1, tab2 = st.tabs(["🎬 Assistente de Produção", "📚 Encontrar Livros"])

    # --- ABA 1: CONSULTORIA TÉCNICA (CHAT - MANTIDO EXATAMENTE IGUAL) ---
    with tab1:
        st.markdown("#### 💬 Chat Técnico")
        st.caption("Descreva seu projeto ou dúvida técnica e a IA buscará a solução nos livros.")
        
        pgt = st.text_input("Qual seu desafio hoje?", placeholder="Ex: Como criar suspense na edição de um filme?", label_visibility="collapsed")
        
        if st.button("Pedir Orientação"):
            if modelo_escolhido and api_key:
                try:
                    ctx = df_base.head(60).to_string(index=False)
                    model = genai.GenerativeModel(modelo_escolhido)
                    
                    prompt = f"""
                    Atue como um Especialista em Produção Cinematográfica (técnico e prático).
                    O usuário quer aprender a fazer filmes. Use este acervo técnico como base: {ctx}.
                    Pergunta do usuário: {pgt}
                    
                    Instruções:
                    1. Explique o conceito de forma prática (mão na massa).
                    2. Indique qual livro do acervo ensina isso melhor.
                    3. Use linguagem moderna e profissional.
                    """
                    
                    with st.spinner("Analisando técnicas de cinema..."):
                        response = model.generate_content(prompt)
                        st.markdown(f"""<div class="ai-card"><div style="font-weight:bold; margin-bottom:10px;">🤖 Resposta do Assistente:</div>{response.text}</div>""", unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Verifique a chave API.")

    # --- ABA 2: BUSCA DE LIVROS (AGORA COM FILTRO INTELIGENTE) ---
    with tab2:
        st.markdown("#### 📚 Acervo Bibliográfico") 
        
        termo = st.text_input("Digite um termo para buscar livros:", placeholder="Ex: iluminação, roteiro, montagem", label_visibility="collapsed")
        btn_pesquisar = st.button("Buscar no Acervo")
        
        if termo:
            termo_limpo = normalizar_texto(termo)
            
            # LISTA DE PALAVRAS PARA IGNORAR (STOPWORDS)
            ignorar = ['livro', 'livros', 'sobre', 'de', 'do', 'da', 'o', 'a', 'em', 'que', 'tem', 'quero', 'gostaria', 'obra', 'obras', 'guia', 'manual']
            
            # Filtra palavras curtas e palavras da lista 'ignorar'
            pals = [p for p in termo_limpo.split() if len(p) > 2 and p not in ignorar]
            
            # Se sobrar alguma palavra, faz a busca
            if pals:
                mask = df_base.apply(lambda r: all(p in normalizar_texto(str(r.values)) for p in pals), axis=1)
                res = df_base[mask]
            else:
                # Se a pessoa digitou só "livros sobre", não busca nada ainda
                res = pd.DataFrame() 
        else:
            res = pd.DataFrame()

        if not res.empty:
            st.caption(f"Encontramos {len(res)} obras:")
            for _, row in res.iterrows():
                c_tit = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
                c_aut = next((c for c in df.columns if 'autor' in c.lower()), "")
                c_res = next((c for c in df.columns if 'resumo' in c.lower()), "")
                c_ct = next((c for c in df.columns if 'categoria' in c.lower()), "")
                
                st.markdown(f"""<div class="book-card">
                    <div style="display:flex; justify-content:space-between;"><b>{row[c_tit]}</b><span class="tag">{row[c_ct]}</span></div>
                    <div style="color:#0066cc; font-size:14px; font-weight:bold;">{row[c_aut]}</div>
                    <div style="font-size:14px; margin-top:5px; color:#333;">{row[c_res]}</div>
                </div>""", unsafe_allow_html=True)
        elif termo:
            # Se filtrou e não achou
            st.info("Nenhum livro encontrado com esse termo exato.")

else:
    st.error("Dados não carregados.")

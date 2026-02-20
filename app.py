import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re
import unicodedata

# --- 1. CONFIGURAÇÃO VISUAL & CSS (O SEU DESIGN ORIGINAL) ---
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

st.markdown("""
<style>
    @media (max-width: 768px) { h1 { font-size: 1.8rem !important; } }
    .block-container { padding-top: 2rem; }
    
    .book-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e0e0e0; margin-bottom: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .ai-card {
        background-color: #f8f9fa; border-left: 5px solid #333; 
        padding: 20px; border-radius: 5px; margin-top: 15px; color: #333;
    }
    
    .stButton>button { 
        background-color: #000; color: white; border-radius: 8px; 
        width: 100%; height: 45px; border: none; font-weight: bold;
    }
    .stButton>button:hover { background-color: #333; color: #fff; }

    h4 { color: #444; margin-bottom: 5px; font-weight: bold; }
    .tag { background: #eee; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; color: #555; }
    .catalog-box { 
        background: #f1f3f4; padding: 10px; border-radius: 6px; 
        font-size: 13px; margin-top: 10px; border-left: 4px solid #000; 
        color: #444;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CONEXÃO API ---
api_key = st.secrets.get("GOOGLE_API_KEY")

# --- 3. FUNÇÕES DE DADOS ---
def normalizar_texto(texto):
    if not isinstance(texto, str): return str(texto).lower()
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

@st.cache_data
def carregar_dados():
    if not os.path.exists("biblioteca.xlsx"): return None
    try:
        # Lê o arquivo e limpa nomes de colunas
        df = pd.read_excel("biblioteca.xlsx")
        # Garante que não pegamos a linha de cabeçalho errada se houver lixo no topo
        if 'Título' not in df.columns:
             df = pd.read_excel("biblioteca.xlsx", header=1)
        
        df.columns = df.columns.str.strip()
        df = df.fillna('')
        return df
    except: return None

df = carregar_dados()

# --- 4. INTERFACE ---
st.title("Acervo Cinema & Artes")

if df is not None:
    # Sidebar com Filtros
    with st.sidebar:
        st.header("🗂️ Filtros")
        col_cat = 'Categoria' if 'Categoria' in df.columns else df.columns[0]
        cat_sel = st.selectbox("Categoria:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(str(x))>2]))
        
        st.divider()
        st.metric("Total de Obras", len(df))
        st.link_button("🔗 Ver Site Online", "https://svai-biblioteca-ia.streamlit.app/")

    # Abas
    tab1, tab2 = st.tabs(["🔎 Pesquisa Visual", "🧠 Consultor IA"])

    with tab1:
        termo = st.text_input("Buscar no acervo:", placeholder="Ex: montagem, godard, teoria")
        
        # Filtro de busca
        df_base = df[df[col_cat] == cat_sel] if cat_sel != "Todas" else df.copy()
        
        if termo:
            termo_n = normalizar_texto(termo)
            mask = df_base.apply(lambda r: termo_n in normalizar_texto(" ".join(map(str, r.values))), axis=1)
            res = df_base[mask]
        else:
            res = df_base.head(10) # Mostra os 10 primeiros por padrão

        st.caption(f"Exibindo {len(res)} obras")

        for _, row in res.iterrows():
            # Pegando os dados de forma segura pelos nomes das colunas
            titulo = row.get('Título', 'Sem Título')
            autor = row.get('Autor', 'Autor Desconhecido')
            resumo = row.get('Resumo', 'Sem resumo disponível.')
            categoria = row.get('Categoria', '')
            cdd = row.get('CDD', '---')
            cutter = row.get('Número de chamada', '---')

            # Renderização do Cartão Bonito
            st.markdown(f"""
                <div class="book-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0; color:#000;">{titulo}</h3>
                        <span class="tag">{categoria}</span>
                    </div>
                    <div style="color:#555; font-weight:500; margin-top:5px;">{autor}</div>
                    <div style="margin-top:10px; font-size:14px; color:#333; line-height:1.5;">{resumo}</div>
                    <div class="catalog-box">
                        <b>📍 Localização Técnica:</b><br>
                        CDD: {cdd} &nbsp;&nbsp; | &nbsp;&nbsp; Número de Chamada: {cutter}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("#### 💬 Consultor Bibliotecário IA")
        pgt = st.text_input("Qual sua dúvida sobre os livros?")
        if st.button("Perguntar à IA"):
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-pro')
                    contexto = df.head(50).to_string()
                    prompt = f"Com base neste acervo: {contexto}. Pergunta: {pgt}"
                    res_ia = model.generate_content(prompt)
                    st.markdown(f'<div class="ai-card"><b>🤖 Resposta:</b><br>{res_ia.text}</div>', unsafe_allow_html=True)
                except: st.error("Erro na API.")
else:
    st.error("Não encontramos o arquivo biblioteca.xlsx.")

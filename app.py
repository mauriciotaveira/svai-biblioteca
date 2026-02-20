import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re
import unicodedata # <--- A VACINA CONTRA ACENTOS

# --- 1. CONFIGURAÇÃO VISUAL & CSS ---
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
    .catalog-box { background: #f1f3f4; padding: 8px; border-radius: 6px; font-size: 12px; margin-top: 10px; border-left: 3px solid #000; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONEXÃO ---
api_key = st.secrets.get("GOOGLE_API_KEY")

# --- 3. DADOS E FUNÇÕES ÚTEIS ---

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return str(texto).lower()
    nfkd = unicodedata.normalize('NFKD', texto)
    texto_sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return texto_sem_acento.lower()

@st.cache_data
def carregar_dados():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not arquivos: return None
    try:
        # Lemos o arquivo (que agora é o 'biblioteca.xlsx' atualizado pelo robô)
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
st.title("Acervo Cinema & Artes")

if df is not None:
    with st.sidebar:
        st.header("⚙️ Motor IA")
        modelo_escolhido = None
        if api_key:
            try:
                genai.configure(api_key=api_key)
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                nomes_limpos = [m.replace('models/', '') for m in modelos]
                st.success("✅ Conectado")
                modelo_escolhido = st.selectbox("Versão do Modelo:", nomes_limpos, index=0)
            except: st.error("Erro na chave API")
        
        st.divider()
        st.header("🗂️ Filtros")
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Categoria:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st.metric("Total de Obras", len(df))
        
        st.divider()
        st.markdown("### 🌐 Link Oficial")
        st.link_button("🔗 Abrir no Navegador", "https://svai-biblioteca-ia.streamlit.app/")

    df_base = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    tab1, tab2 = st.tabs(["🔎 Pesquisa Visual", "🧠 Consultor IA"])

    with tab1:
        st.markdown("#### 🔎 Explorar Acervo") 
        termo = st.text_input("Digite palavras-chave:", placeholder="Ex: ficcao, edicao, roteiro", label_visibility="collapsed")
        
        if termo:
            termo_limpo = normalizar_texto(termo)
            pals = [p for p in termo_limpo.split() if len(p) > 2]
            mask = df_base.apply(lambda r: all(p in normalizar_texto(str(r.values)) for p in pals), axis=1)
            res = df_base[mask]
        else:
            res = pd.DataFrame()

        if not res.empty:
            st.caption(f"Encontrados: {len(res)}")
            for _, row in res.iterrows():
                # IDENTIFICAÇÃO DAS COLUNAS
                c_tit = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
                c_aut = next((c for c in df.columns if 'autor' in c.lower()), "")
                c_res = next((c for c in df.columns if 'resumo' in c.lower()), "")
                c_ct = next((c for c in df.columns if 'categoria' in c.lower()), "")
                # COLUNAS DO ROBÔ
                c_cdd = next((c for c in df.columns if 'cdd' in c.lower()), "")
                c_cham = next((c for c in df.columns if 'número de chamada' in c.lower() or 'chamada' in c.lower()), "")
                
                # MONTAGEM DO CARD (AJUSTADO)
                st.markdown(f"""<div class="book-card">
                    <div style="display:flex; justify-content:space-between;"><b>{row[c_tit]}</b><span class="tag">{row[c_ct]}</span></div>
                    <div style="color:blue; font-size:14px;">{row[c_aut]}</div>
                    <div style="font-size:14px; margin-top:8px; color:#333; line-height:1.4;">{row[c_res]}</div>
                    <div class="catalog-box">
                        <b>📍 Catalogação:</b> CDD {row[c_cdd]} | <b>Cutter:</b> {row[c_cham]}
                    </div>
                </div>""", unsafe_allow_html=True)
        elif termo:
            st.info("Nenhum resultado encontrado.")

    with tab2:
        st.markdown("#### 💬 Chat Inteligente")
        pgt = st.text_input("Sua dúvida:", placeholder="Ex: Qual a importância da montagem segundo os livros?", key="chat_input", label_visibility="collapsed")
        
        if st.button("Consultar"):
            if modelo_escolhido and api_key:
                try:
                    ctx = df_base.head(60).to_string(index=False)
                    model = genai.GenerativeModel(modelo_escolhido)
                    prompt = f"Atue como um bibliotecário especialista. Use: {ctx}. Pergunta: {pgt}"
                    
                    with st.spinner("Consultando..."):
                        response = model.generate_content(prompt)
                        st.markdown(f"""<div class="ai-card"><b>🤖 Resposta:</b><br>{response.text}</div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erro: {e}")

else:
    st.error("Dados não carregados.")

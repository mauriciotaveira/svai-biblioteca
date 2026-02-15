import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re

# --- 1. CONFIGURAÇÃO VISUAL & CSS AVANÇADO ---
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

st.markdown("""
<style>
    /* Ajuste Mobile para Títulos */
    @media (max-width: 768px) {
        h1 { font-size: 1.8rem !important; }
        .titulo-tab { font-size: 1rem !important; }
    }

    .block-container { padding-top: 2rem; }
    
    /* Cartão dos Livros */
    .book-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #f0f0f0; margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .book-card:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 8px 16px rgba(0,0,0,0.1); 
        border-color: #ddd;
    }
    
    /* Cartão da Resposta da IA */
    .ai-card {
        background-color: #f8f9fa; 
        border-left: 4px solid #333; 
        padding: 20px; 
        border-radius: 4px;
        font-family: 'Helvetica', sans-serif;
        color: #333;
        margin-top: 15px;
    }
    .ai-card h3 { font-size: 16px; font-weight: bold; margin-top: 15px; margin-bottom: 10px; color: #000; }
    .ai-card strong { color: #000; }
    .ai-card ul { margin-left: 20px; }
    
    /* Botões - Correção do Hover */
    .stButton>button { 
        background-color: #111; 
        color: white; 
        border-radius: 8px; 
        width: 100%; 
        height: 48px; /* Altura igual ao input */
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background-color: #333 !important; /* Cinza escuro no hover */
        color: #fff !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .stButton>button:active {
        background-color: #000 !important;
    }

    /* Tags de Categoria */
    .tag { background: #eee; padding: 3px 10px; border-radius: 12px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: bold; color: #555; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONEXÃO ---
api_key = st.secrets.get("GOOGLE_API_KEY")

# --- 3. DADOS ---
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
st.title("Acervo Cinema & Artes")

if df is not None:
    # Sidebar Inteligente
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

    # Filtragem Base
    df_base = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    # Abas com nomes modernos
    tab1, tab2 = st.tabs(["🔎 Explorar Acervo", "🧠 Assistente Virtual"])

    # --- ABA 1: EXPLORAR (PESQUISA VISUAL) ---
    with tab1:
        # Layout: Input (3 partes) + Botão (1 parte)
        col_busca, col_btn = st.columns([4, 1])
        
        with col_busca:
            termo = st.text_input("O que você procura?", placeholder="Ex: montagem, roteiro, direção...", label_visibility="collapsed")
        
        with col_btn:
            btn_pesquisar = st.button("Buscar 🔎")

        # Lógica de Busca Aprimorada (Stopwords)
        res = pd.DataFrame() # Começa vazio
        
        if termo or btn_pesquisar:
            # Lista de palavras para ignorar na busca
            ignorar = ['o','a','de','do','da','em','um','uma','sobre','livros','livro','obra','obras','tem','quais','existe','quero']
            
            # Limpa o termo digitado
            pals = [p for p in termo.lower().split() if p not in ignorar]
            
            if not pals: # Se a pessoa digitou só "livros sobre", não busca nada ainda
                st.warning("Digite um tema específico (ex: Cinema, Arte, Hitchcock)")
            else:
                mask = df_base.apply(lambda r: all(p in r.astype(str).str.lower().str.cat(sep=' ') for p in pals), axis=1)
                res = df_base[mask]

        # Exibição dos Resultados
        if res.empty:
            if termo:
                st.info("Nenhum resultado encontrado para essa busca específica.")
            else:
                st.markdown("<div style='text-align:center; color:gray; margin-top:50px;'>Digite um tema acima para começar a explorar o acervo.</div>", unsafe_allow_html=True)
        else:
            st.caption(f"Encontrados: {len(res)}")
            for _, row in res.iterrows():
                c_tit = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
                c_aut = next((c for c in df.columns if 'autor' in c.lower()), "")
                c_res = next((c for c in df.columns if 'resumo' in c.lower()), "")
                c_ct = next((c for c in df.columns if 'categoria' in c.lower()), "")
                
                st.markdown(f"""<div class="book-card">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <span style="font-weight:bold; font-size:16px;">{row[c_tit]}</span>
                        <span class="tag">{row[c_ct]}</span>
                    </div>
                    <div style="color:#007bff; font-size:13px; margin: 4px 0 8px 0;">{row[c_aut]}</div>
                    <div style="font-size:14px; color:#444; line-height:1.4;">{row[c_res]}</div>
                </div>""", unsafe_allow_html=True)

    # --- ABA 2: ASSISTENTE VIRTUAL ---
    with tab2:
        st.markdown("#### 💬 Chat Inteligente") # Fonte menor (h4)
        st.caption("Pergunte sobre conceitos, autores ou peça recomendações baseadas no acervo.")
        
        pgt = st.text_input("Digite sua dúvida aqui:", placeholder="Ex: Qual a diferença entre corte e plano segundo os livros?")
        
        if st.button("Enviar Pergunta"):
            if modelo_escolhido and api_key:
                # Se não houve busca visual antes, usa o DF base, senão usa o resultado da busca
                # Mas para IA ser boa, melhor dar contexto amplo se a busca for vazia
                contexto_df = res if not res.empty else df_base.head(50) 
                ctx = contexto_df.to_string(index=False)
                
                try:
                    model = genai.GenerativeModel(modelo_escolhido)
                    
                    prompt = f"""
                    Atue como um especialista em cinema e artes.
                    Baseado EXCLUSIVAMENTE nestes dados do acervo: {ctx}. 
                    Pergunta do usuário: {pgt}
                    
                    Instruções de Estilo:
                    1. Responda de forma direta e elegante.
                    2. Use Markdown: **Negrito** para autores/obras, Listas para tópicos.
                    3. Se a resposta não estiver nos livros, diga que não consta no acervo atual.
                    """
                    
                    with st.spinner("Analisando acervo..."):
                        response = model.generate_content(prompt)
                        
                        st.markdown(f"""
                        <div class="ai-card">
                            <div style="margin-bottom:10px; font-weight:bold; color:#555;">🤖 Resposta:</div>
                            {response.text} 
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Configure a chave API na barra lateral.")
else:
    st.error("Dados não carregados.")

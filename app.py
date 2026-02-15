import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re

# --- 1. CONFIGURAÇÃO VISUAL & CSS (Mantendo apenas correções essenciais) ---
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

st.markdown("""
<style>
    /* Ajuste para celular (Título menor) */
    @media (max-width: 768px) {
        h1 { font-size: 1.8rem !important; }
    }

    .block-container { padding-top: 2rem; }
    
    /* Cartão dos Livros */
    .book-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e0e0e0; margin-bottom: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Cartão da Resposta da IA */
    .ai-card {
        background-color: #f8f9fa; 
        border-left: 5px solid #333; 
        padding: 20px; 
        border-radius: 5px;
        margin-top: 15px;
        color: #333;
    }
    
    /* Botões (Correção para não sumir no hover) */
    .stButton>button { 
        background-color: #000; 
        color: white; 
        border-radius: 8px; 
        width: 100%; 
        height: 45px; 
        border: none;
    }
    .stButton>button:hover { 
        background-color: #333; 
        color: #fff;
    }

    .tag { background: #eee; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; color: #555; }
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
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Motor IA")
        modelo_escolhido = None
        if api_key:
            try:
                genai.configure(api_key=api_key)
                # Lista modelos (Lógica que funcionou)
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

    # Dataframe Base (Filtrado por categoria ou Inteiro)
    df_base = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    tab1, tab2 = st.tabs(["🔎 Pesquisa Visual", "🧠 Consultor IA"])

    # --- ABA 1: PESQUISA VISUAL (Lógica Restaurada) ---
    with tab1:
        col_busca, col_btn = st.columns([4, 1])
        with col_busca:
            termo = st.text_input("Buscar no acervo:", placeholder="Ex: montagem cinema", label_visibility="collapsed")
        with col_btn:
            st.write("") # Espaço vazio para alinhar

        # Lógica Simples (A que funcionava)
        if termo:
            # Pega as palavras, mas sem lista de proibição agressiva
            pals = [p for p in termo.lower().split() if len(p) > 2] # Ignora apenas palavras de 1 ou 2 letras (o, a, de)
            mask = df_base.apply(lambda r: all(p in r.astype(str).str.lower().str.cat(sep=' ') for p in pals), axis=1)
            res = df_base[mask]
        else: 
            # Se não tem termo, NÃO MOSTRA NADA (Pedido seu)
            res = pd.DataFrame()

        # Exibição
        if not res.empty:
            st.caption(f"Encontrados: {len(res)}")
            for _, row in res.iterrows():
                c_tit = next((c for c in df.columns if 'título' in c.lower() or 'titulo' in c.lower()), df.columns[0])
                c_aut = next((c for c in df.columns if 'autor' in c.lower()), "")
                c_res = next((c for c in df.columns if 'resumo' in c.lower()), "")
                c_ct = next((c for c in df.columns if 'categoria' in c.lower()), "")
                
                st.markdown(f"""<div class="book-card">
                    <div style="display:flex; justify-content:space-between;"><b>{row[c_tit]}</b><span class="tag">{row[c_ct]}</span></div>
                    <div style="color:blue; font-size:14px;">{row[c_aut]}</div>
                    <div style="font-size:14px; margin-top:5px; color:#333;">{row[c_res]}</div>
                </div>""", unsafe_allow_html=True)
        elif termo:
            st.info("Nenhum resultado encontrado para esta combinação exata.")

    # --- ABA 2: CONSULTOR IA (Contexto Ampliado) ---
    with tab2:
        st.markdown("#### 💬 Chat Inteligente")
        pgt = st.text_input("Sua dúvida:", placeholder="Ex: Qual a importância da montagem segundo os livros?")
        
        if st.button("Consultar"):
            if modelo_escolhido and api_key:
                try:
                    # AQUI ESTÁ A CORREÇÃO PRINCIPAL:
                    # Em vez de olhar só para a busca (que pode estar vazia ou errada),
                    # a IA olha para os primeiros 60 livros da categoria inteira.
                    # Isso garante que ela tenha "conteúdo" para gerar a resposta rica.
                    ctx = df_base.head(60).to_string(index=False)
                    
                    model = genai.GenerativeModel(modelo_escolhido)
                    
                    prompt = f"""
                    Atue como um bibliotecário especialista em cinema e artes.
                    Use estes livros do acervo como base para sua resposta: {ctx}.
                    
                    Pergunta do usuário: {pgt}
                    
                    Instruções:
                    1. Seja detalhado, educativo e elegante (como um professor universitário).
                    2. Cite os livros e autores do acervo que se relacionam com a pergunta.
                    3. Use Markdown para formatar (Negrito, Listas) para facilitar a leitura.
                    4. Se a pergunta for ampla (ex: "fale sobre montagem"), faça uma dissertação rica usando vários livros.
                    """
                    
                    with st.spinner("O Bibliotecário está consultando o acervo..."):
                        response = model.generate_content(prompt)
                        
                        st.markdown(f"""
                        <div class="ai-card">
                            <div style="font-weight:bold; margin-bottom:10px;">🤖 Resposta:</div>
                            {response.text} 
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Verifique a chave API.")
else:
    st.error("Dados não carregados.")

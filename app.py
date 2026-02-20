import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re
import unicodedata

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA", page_icon="🎬", layout="wide")

# --- 2. CSS FINAL (BLINDADO CONTRA ERROS DE CÓPIA) ---
css_code = (
    "<style>\n"
    ".stApp { background-color: #ffffff !important; }\n"
    "div.stButton > button { background-color: #000000 !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; }\n"
    "div.stButton > button:hover { background-color: #333333 !important; color: #ffffff !important; }\n"
    "div.stButton > button p { color: #ffffff !important; }\n"
    "h1, h2, h3, h4, h5, h6, .stMarkdown p, .stMarkdown li, label, div { color: #000000 !important; }\n"
    ".stTextInput input { color: #000000 !important; background-color: #ffffff !important; border: 1px solid #ccc !important; }\n"
    "::placeholder { color: #888888 !important; font-style: italic !important; opacity: 1 !important; }\n"
    ".titulo-tech { font-family: 'Helvetica', sans-serif; color: #000000 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 5px; line-height: 1.0; letter-spacing: -1px; }\n"
    ".subtitulo-tech { font-family: 'Helvetica', sans-serif; color: #444444 !important; font-size: 1.2rem; margin-bottom: 25px; }\n"
    ".box-instrucao { background-color: #f0f7ff !important; padding: 15px; border-radius: 8px; border-left: 6px solid #0066cc; color: #333333 !important; font-size: 1rem; margin-bottom: 30px; }\n"
    ".destaque-tech { font-weight: bold; color: #0066cc !important; }\n"
    ".book-card { background: white !important; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }\n"
    ".book-card b, .book-card span { color: #000000 !important; }\n"
    ".ai-card { background-color: #f8f9fa !important; border-left: 5px solid #333; padding: 15px; border-radius: 5px; margin-top: 15px; color: #000000 !important; }\n"
    "@media (max-width: 768px) { .titulo-tech { font-size: 2.5rem !important; } }\n"
    "</style>"
)
st.markdown(css_code, unsafe_allow_html=True)

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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.secrets.get("GOOGLE_API_KEY")
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
    if df is not None:
        col_cat = next((c for c in df.columns if 'categoria' in c.lower()), None)
        cat_sel = st.selectbox("Filtrar Área:", ["Todas"] + sorted([x for x in df[col_cat].unique() if len(x)>2])) if col_cat else "Todas"
        st.metric("Obras", len(df))
        st.divider()
        st.link_button("🔗 Abrir App", "https://svai-biblioteca-ia.streamlit.app/")

# --- 5. INTERFACE ---
st.markdown('<div class="titulo-tech">Cine.IA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo-tech">Inteligência para Criar Filmes</div>', unsafe_allow_html=True)

caixa_instrucao = (
    '<div class="box-instrucao">'
    '🤖 <b>Seu Assistente de Produção</b><br>'
    'Pergunte: "Como <span class="destaque-tech">financiar um curta</span>?", '
    '"Regra dos <span class="destaque-tech">180 graus</span>" ou '
    '"Dicas de <span class="destaque-tech">iluminação</span>".'
    '</div>'
)
st.markdown(caixa_instrucao, unsafe_allow_html=True)

if df is not None:
    df_base = df[df[col_cat] == cat_sel] if cat_sel != "Todas" and col_cat else df.copy()
    
    tab1, tab2 = st.tabs(["🎬 Assistente de Produção", "📚 Buscar Livros"])

    # --- ABA 1: O CHAT INTELIGENTE (AGORA COM RANKING E CATALOGAÇÃO!) ---
    with tab1:
        st.markdown("<small style='color:#666; font-style:italic;'>Ex: 'Como criar suspense?' ou 'Técnicas de roteiro'</small>", unsafe_allow_html=True)
        pgt = st.text_input("Dúvida", placeholder="Digite sua dúvida aqui...", label_visibility="collapsed")
        
        if st.button("Pedir Orientação"):
            if modelo_escolhido and api_key:
                try:
                    pgt_norm = normalizar_texto(pgt)
                    ignorar = ['como', 'fazer', 'o', 'que', 'e', 'um', 'uma', 'de', 'do', 'da', 'para', 'com', 'livro', 'sobre']
                    palavras = [p for p in pgt_norm.split() if p not in ignorar and len(p) > 2]
                    
                    if not palavras: palavras = pgt_norm.split()
                    
                    def pontuar(row):
                        txt = normalizar_texto(str(row))
                        return sum(1 for p in palavras if p in txt)

                    df_base['score'] = df_base.apply(lambda r: pontuar(r.values), axis=1)
                    melhores = df_base.sort_values('score', ascending=False).head(20)
                    ctx = melhores.to_string(index=False)
                    
                    model = genai.GenerativeModel(modelo_escolhido)
                    
                    # PROMPT BLINDADO (SEM ASPAS TRIPLAS)
                    prompt_ia = (
                        "Atue como o Cine.IA, um Especialista em Cinema, operando com o rigor acadêmico de um Bibliotecário Chefe Catalogador.\n"
                        f"Você tem acesso a este ACERVO DE LIVROS selecionados:\n{ctx}\n\n"
                        f"Pergunta do Usuário: {pgt}\n\n"
                        "Instruções:\n"
                        "1. Responda à dúvida técnica de forma didática.\n"
                        "2. CITE OS LIVROS DO ACERVO que ajudam nesse tema.\n"
                        "3. OBRIGATORIAMENTE, crie uma seção no final chamada 'REFERÊNCIAS CATALOGRÁFICAS'.\n\n"
                        "REGRAS RÍGIDAS DE FORMATAÇÃO (ABNT + CATALOGAÇÃO DE ESTANTE):\n"
                        "Para cada livro citado, você deve apresentar:\n"
                        "- A Referência ABNT: SOBRENOME DO AUTOR, Nome. Título da obra. Local: Editora, Ano. (Use [S.l.] e [s.d.] se faltar dado).\n"
                        "- CDD (Classificação Decimal de Dewey): Atribua o número CDD correto baseado no tema do livro (Ex: Cinema é 791.43).\n"
                        "- Número de Chamada: Crie o número de chamada completo usando a Tabela Cutter-Sanborn.\n\n"
                        "Exemplo de saída esperada:\n"
                        "COUSINS, Mark. História do Cinema. [S.l.]: Martins Fontes, [s.d.].\n"
                        "CDD: 791.4309\n"
                        "Chamada: 791.4309 C836h\n"
                    )

                    with st.spinner("Consultando biblioteca técnica..."):
                        response = model.generate_content(prompt_ia)
                        resposta_html = f'<div class="ai-card"><b>🤖 Resposta:</b><br>{response.text}</div>'
                        st.markdown(resposta_html, unsafe_allow_html=True)
                        
                except Exception as e: st.error(f"Erro: {e}")
            else: st.error("Erro API")

    # --- ABA 2: BUSCA MANUAL (PRONTA PARA CDD E CHAMADA) ---
    with tab2:
        st.markdown("<small style='color:#666; font-style:italic;'>Ex: 'montagem', 'iluminação', 'som'</small>", unsafe_allow_html=True)
        termo = st.text_input("Busca", placeholder="Digite um termo...", label_visibility="collapsed")
        
        def formatar_autor_abnt(autor):
            if not autor or str(autor).strip() == "" or str(autor).lower() == "nan": 
                return "[Autor Desconhecido]"
            partes = str(autor).strip().split()
            if len(partes) == 1: 
                return partes[0].upper()
            sobrenome = partes[-1].upper()
            resto = " ".join(partes[:-1])
            return f"{sobrenome}, {resto}"

        if st.button("Buscar"):
            if termo:
                termo_limpo = normalizar_texto(termo)
                ignorar = ['livro', 'sobre', 'de', 'do', 'que', 'tem', 'quero']
                pals = [p for p in termo_limpo.split() if len(p) > 2 and p not in ignorar]
                
                if pals:
                    mask = df_base.apply(lambda r: all(p in normalizar_texto(str(r.values)) for p in pals), axis=1)
                    res = df_base[mask]
                    if not res.empty:
                        
                        cols = [str(c).lower() for c in df_base.columns]
                        idx_cdd = next((i for i, c in enumerate(cols) if 'cdd' in c or 'classificação' in c), None)
                        idx_chamada = next((i for i, c in enumerate(cols) if 'chamada' in c or 'cutter' in c), None)
                        
                        for _, row in res.iterrows():
                            vals = row.values
                            
                            c_tit = str(vals[0]).strip()
                            c_aut = str(vals[1]).strip() if len(vals) > 1 else ""
                            c_editora = str(vals[2]).strip() if len(vals) > 2 else ""
                            c_res = str(vals[4]).strip() if len(vals) > 4 else ""
                            
                            c_cdd = str(vals[idx_cdd]).strip() if idx_cdd is not None and len(vals) > idx_cdd else "[Sem CDD no Acervo]"
                            c_chamada = str(vals[idx_chamada]).strip() if idx_chamada is not None and len(vals) > idx_chamada else "[Sem Chamada no Acervo]"
                            
                            if c_editora.lower() in ['nan', '', 'falta editora']: c_editora = "[s.n.]"
                            if c_cdd.lower() in ['nan', '']: c_cdd = "[Sem CDD no Acervo]"
                            if c_chamada.lower() in ['nan', '']: c_chamada = "[Sem Chamada no Acervo]"
                            
                            c_ano = "[s.d.]"
                            c_cidade = "[S.l.]"
                            
                            autor_abnt = formatar_autor_abnt(c_aut)
                            citacao_abnt = f"{autor_abnt}. <b>{c_tit}</b>. {c_cidade}: {c_editora}, {c_ano}."
                            
                            html_card = (
                                f'<div class="book-card">'
                                f'<p style="margin-bottom: 5px; font-size: 15px; color: #000;">{citacao_abnt}</p>'
                                f'<div style="background-color: #f0f0f0; padding: 5px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #555; margin-bottom: 10px;">'
                                f'<b>CDD:</b> {c_cdd} | <b>Chamada:</b> {c_chamada}'
                                f'</div>'
                                f'<hr style="margin: 5px 0; border-top: 1px solid #eee;">'
                                f'<p style="font-size:13px; color: #333; margin-top: 10px;"><b>Resumo:</b> {c_res}</p>'
                                f'</div>'
                            )
                            st.markdown(html_card, unsafe_allow_html=True)
                            
                    else: st.info("Nada encontrado.")
                else: st.warning("Digite um termo mais específico.")

else: st.error("Excel não carregado.")

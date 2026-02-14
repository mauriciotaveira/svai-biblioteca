import streamlit as st
import pandas as pd
import google.generativeai as genai
import unicodedata
import re
import streamlit as st
import pandas as pd
# ... outros imports ...

import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira linha!)
st.set_page_config(page_title="Acervo de Cinema & Artes", layout="wide")

# 2. DESIGN "CINEMA PRO" + AJUSTES MOBILE (CSS UNIFICADO)
st.markdown("""
    <style>
    /* Fundo e Fonte */
    .stApp { background-color: #FFFFFF; color: #1A1A1A; font-family: 'Inter', sans-serif; }
    
    /* Remove espaço branco excessivo do topo (Crítico para Mobile) */
    .block-container { padding-top: 2rem !important; padding-bottom: 0rem !important; }

    /* Esconde Menu e Rodapé padrão (Mais profissional) */
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}

    /* BOTÕES PRETOS ELEGANTES (Seu estilo Cinema Pro) */
    div.stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        height: 48px !important;
        width: 100%;
        font-weight: 700 !important;
    }
    div.stButton > button:hover {
        background-color: #333333 !important; /* Cinza escuro no hover */
    }

    /* ESTILO DO MENU DE OPÇÕES (RADIO BUTTONS) */
    div[role="radiogroup"] {
        background-color: #F8F9FA;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. CABEÇALHO LIMPO E INSTRUCIONAL
st.markdown("""
    <div style="margin-bottom: 15px;">
        <h1 style='text-align: left; color: #1E1E1E; font-size: 2.2rem; margin-bottom: 5px;'>
            Acervo de Cinema e Artes
        </h1>
        <p style='text-align: left; color: #555; font-size: 1.0rem; line-height: 1.5;'>
            Bem-vindo. Selecione abaixo se deseja <b>pesquisar itens</b> no acervo 
            ou conversar com nosso <b>Consultor IA</b>.
        </p>
    </div>
""", unsafe_allow_html=True)

# 4. NAVEGAÇÃO CLARA (SUBSTITUI OS LINKS CONFUSOS)
# Cria botões lado a lado para alternar as telas
modo_uso = st.radio(
    "Navegação:", 
    ["🔍 Busca na Coleção", "🤖 Consultor Estratégico"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider() # Linha fina e elegante

# --- INÍCIO DA LÓGICA ---

if modo_uso == "🔍 Busca na Coleção":
    
    # 5. FILTROS NO TOPO (Coluna Única - Mobile First)
    st.write("### 📂 Filtrar Acervo") # Subtítulo pequeno
    
    # Multiselect ocupa a largura total, perfeito para celular e desktop
    categorias = st.multiselect(
        "Selecione as áreas de interesse:",
        options=["Antropologia", "Artes", "Audiovisual", "Cinema", "Ciência Política"],
        default=["Cinema", "Artes"],
        placeholder="Escolha as categorias..."
    )
    
    # Espaço para o Input de Busca...
    termo_busca = st.text_input("Digite termo, autor ou título:", placeholder="Ex: Nouvelle Vague...")
    
    # Botão de Ação com o seu estilo "Cinema Pro"
    if st.button("PESQUISAR NO ACERVO"):
        st.write(f"Buscando por: {termo_busca} nas categorias {categorias}...")
        # Coloque aqui a lógica de busca do DataFrame...

elif modo_uso == "🤖 Consultor Estratégico":
    st.info("💡 O Consultor sVAI utiliza IA para cruzar referências e sugerir leituras.")
    
    user_question = st.text_input("Qual sua dúvida sobre o tema?", placeholder="Ex: Livros sobre montagem soviética...")
    
    if st.button("ANALISAR AGORA"):
        # Lógica do Gemini aqui...
        pass

# --- 3. FUNÇÕES ---
def normalizar(texto):
    if not isinstance(texto, str): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^\w\s]', ' ', texto)
    return texto.lower().strip()

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Minha biblioteca.csv', sep=';', skiprows=1)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.fillna("Não informado")
        df['Categoria'] = df['Categoria'].astype(str).apply(lambda x: x.split('+')[0].strip())
        df['search_field'] = df.apply(lambda x: normalizar(f"{x['Título']} {x['Autor']} {x['Categoria']} {x['Resumo']} {x['Palavras-Chave']}"), axis=1)
        return df
    except: return pd.DataFrame()

df = load_data()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("sVai Library")
    st.markdown("---")
    
    st.markdown("### ⚙️ Motor da IA")
    # CONFIGURAÇÃO IGUAL AO VÍDEO 1
    modelo_selecionado = st.selectbox(
        "Versão do Modelo:",
        ["models/gemini-2.5-flash", "models/gemini-1.5-pro", "models/gemini-1.5-flash"],
        index=0 # Padrão é o que funciona no vídeo
    )
    
    # Espaço visual
    st.write("") 
    
    if st.button("REINICIAR"):
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏛️ CATEGORIAS")
    if not df.empty:
        for c in sorted(df['Categoria'].unique()):
            if c != "Não informado": st.markdown(f"• {c}")

# --- 5. CONFIGURAÇÃO IA ---
api_key = st.secrets.get("GEMINI_API_KEY")
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(modelo_selecionado)
    except Exception: pass

# --- 6. INTERFACE ---
st.title("Classificação via IA")
tab1, tab2 = st.tabs(["🔍 Busca na Coleção", "🧠 Consultor Estratégico"])

with tab1:
    busca = st.text_input("Localizar obra:", placeholder="Ex: montagem, cinema...")
    
    if busca:
        b_norm = normalizar(busca)
        
        # LISTA DE STOPWORDS (Palavras para ignorar)
        palavras_ignoradas = [
            "o", "a", "os", "as", "um", "uma", "uns", "umas",
            "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
            "por", "para", "com", "sem", "tem", "ter", "tinha",
            "livro", "livros", "obra", "obras", "sobre", "acerca",
            "quero", "gostaria", "preciso", "procura", "busco",
            "quais", "qual", "quem", "onde", "como", "quando",
            "que", "se", "eh", "sao", "foi"
        ]
        
        # Filtra a busca: só deixa passar o que NÃO está na lista proibida
        termos_validos = [p for p in b_norm.split() if p not in palavras_ignoradas and len(p) > 1]
        
        # Se o usuário digitou só "livros sobre", sobra vazio -> não busca nada.
        if not termos_validos:
            st.warning("Por favor, digite um tema específico (ex: 'cinema', 'peixes', 'montagem').")
        else:
            # LÓGICA E (AND): O livro precisa ter TODOS os termos válidos restantes
            # Ex: "Montagem do filme" -> Sobra "Montagem", "Filme". O livro tem que ter os dois.
            mask = df['search_field'].apply(lambda x: all(termo in x for termo in termos_validos))
            res = df[mask]
            
            if not res.empty:
                st.write(f"Resultados: **{len(res)}**")
                for _, row in res.iterrows():
                    st.markdown(f"""<div class="book-card">
                        <span style='color: #800000; font-weight: 800;'>{row['Categoria']}</span>
                        <h3>{row['Título']}</h3>
                        <p><b>{row['Autor']}</b></p>
                        <p style='color: #444;'>{row['Resumo']}</p>
                    </div>""", unsafe_allow_html=True)
            else:
                # Mensagem inteligente se não achar nada
                termo_exibicao = " ".join(termos_validos).upper()
                st.warning(f"Nenhuma obra encontrada contendo: **{termo_exibicao}**")

with tab2:
    st.subheader("Consultor sVai")
    pergunta = st.text_input("Sua dúvida:", placeholder="Quais livros falam sobre montagem?")
    
    if st.button("ANALISAR AGORA"):
        if pergunta:
            with st.spinner(f"Processando com {modelo_selecionado}..."):
                try:
                    p_norm = normalizar(pergunta)
                    # Mesma lógica de stopwords para a IA achar o contexto
                    termos = [p for p in p_norm.split() if len(p) > 3] # Filtro simples p/ IA
                    mask_ia = df['search_field'].apply(lambda x: any(p in x for p in termos))
                    match = df[mask_ia].head(25) # Contexto rico
                    
                    if match.empty:
                        st.info("Não encontrei livros suficientes no acervo para basear a resposta.")
                    else:
                        dados = "\n".join([f"- {r['Título']} ({r['Autor']}): {r['Resumo']}" for _, r in match.iterrows()])
                        prompt = f"""
                        Atue como Consultor Especialista.
                        ACERVO DISPONÍVEL:
                        {dados}
                        
                        PERGUNTA DO USUÁRIO: {pergunta}
                        
                        Responda com base ESTRITAMENTE no acervo acima.
                        """
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
                except Exception as e:
                    st.error(f"Erro: {e}")
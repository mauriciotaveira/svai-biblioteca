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

import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# 2. DESIGN LIMPO (CSS)
st.markdown("""
    <style>
    /* Fundo branco e fonte profissional */
    .stApp { background-color: #FFFFFF; color: #1A1A1A; font-family: 'Inter', sans-serif; }
    
    /* Removemos o padding excessivo do topo */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }

    /* Esconde menu e rodapé */
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}

    /* BOTÃO PRETO (Estilo Cinema) */
    div.stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        height: 45px !important;
        font-weight: 600 !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
    }

    /* Ajuste dos Inputs para parecerem clicáveis de verdade */
    .stTextInput > div > div {
        border: 1px solid #ced4da;
        border-radius: 6px;
    }
    
    /* Ajuste do Multiselect para não cortar texto */
    .stMultiSelect span {
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# 3. CABEÇALHO (Título Grande + Descrição Pequena)
st.markdown("""
    <div style="margin-bottom: 10px;">
        <h1 style='text-align: left; color: #000; font-size: 1.8rem; margin-bottom: 5px; font-weight: 700;'>
            Acervo de Cinema e Artes
        </h1>
        <p style='text-align: left; color: #666; font-size: 0.95rem; margin-top: 0;'>
            Utilize os filtros abaixo para navegar na coleção ou o Consultor para perguntas complexas.
        </p>
    </div>
""", unsafe_allow_html=True)

# 4. SELETOR DE MODO (Simples e Direto)
modo_uso = st.radio(
    "Modo de Operação:", 
    ["🔍 Busca Rápida", "🤖 Consultor IA"],
    horizontal=True,
    label_visibility="collapsed"
)

st.write("") # Espaço em branco (Respiro real, sem linhas falsas)

# --- LÓGICA DE UMA COLUNA SÓ (FULL WIDTH) ---

if modo_uso == "🔍 Busca Rápida":
    
    # RÓTULO PEQUENO (Substitui o texto gigante)
    st.markdown("<p style='font-size: 0.85rem; color: #555; font-weight: 600; margin-bottom: 5px;'>FILTRAR CATEGORIAS & TEMAS</p>", unsafe_allow_html=True)
    
    # CATEGORIAS (Ocupando largura total)
    categorias = st.multiselect(
        "Categorias",
        options=["Antropologia", "Artes", "Audiovisual", "Cinema", "Ciência Política", "Sociologia", "História"],
        default=None, # Sem padrão, para o usuário ver o placeholder
        placeholder="Clique para selecionar (Ex: Cinema, Artes...)",
        label_visibility="collapsed"
    )
    
    st.write("") # Respiro
    
    # CAMPO DE BUSCA (Claramente um input)
    termo_busca = st.text_input(
        "Busca",
        placeholder="Digite o termo de busca aqui...",
        label_visibility="collapsed"
    )
    
    st.write("") # Respiro
    
    # BOTÃO DE AÇÃO
    if st.button("PESQUISAR"):
        if not termo_busca and not categorias:
            st.warning("Por favor, digite um termo ou selecione uma categoria.")
        else:
            st.success(f"Buscando '{termo_busca}'...")
            # Lógica de filtro do DataFrame aqui

elif modo_uso == "🤖 Consultor IA":
    st.markdown("<p style='font-size: 0.85rem; color: #555; font-weight: 600; margin-bottom: 5px;'>INTELIGÊNCIA ARTIFICIAL</p>", unsafe_allow_html=True)
    
    st.info("💡 Pergunte ao acervo como se falasse com um bibliotecário.")
    
    user_question = st.text_input("Sua dúvida:", placeholder="Ex: Qual a influência da Nouvelle Vague no cinema brasileiro?")
    
    if st.button("ANALISAR PERGUNTA"):
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
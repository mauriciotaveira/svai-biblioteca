import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA - Gestão de Acervo", layout="wide")

st.markdown("""
<style>
    .book-card {
        background: white; padding: 18px; border-radius: 10px;
        border: 1px solid #e0e0e0; margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); min-height: 250px;
    }
    .cdd-box {
        background-color: #f8f9fa; padding: 8px; border-radius: 5px;
        font-family: monospace; font-size: 12px; color: #333;
        border-left: 4px solid #000; margin-top: 10px;
    }
    .abnt-text { font-size: 10px; color: #888; margin-top: 10px; font-style: italic; }
    .guide-box { background-color: #fff3cd; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; color: #856404; }
</style>
""", unsafe_allow_html=True)

# --- 2. CARREGAR DADOS ---
@st.cache_data
def load_data():
    if not os.path.exists("biblioteca.xlsx"): return None
    df = pd.read_excel("biblioteca.xlsx")
    df.columns = df.columns.str.strip()
    return df.fillna("")

df = load_data()

st.title("🎬 Cine.IA - Acervo de Cinema")

if df is not None:
    # --- AS DUAS ABAS COM OS NOMES CORRETOS ---
    tab1, tab2 = st.tabs(["🤖 Assistente de Produção", "🔎 Buscar Palavras-Chave"])

    with tab1:
        st.markdown("""
        <div class="guide-box">
            <h4>Como navegar no Assistente:</h4>
            <ul>
                <li>Use este espaço para tirar dúvidas teóricas sobre o acervo.</li>
                <li>Digite uma pergunta sobre cinema, autores ou conceitos técnicos.</li>
                <li>A IA consultará a base de dados para te dar uma resposta fundamentada.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        pergunta = st.text_area("Sua dúvida para o Assistente:", placeholder="Ex: Quais livros falam sobre montagem dialética?")
        
        if st.button("Consultar Inteligência Artificial"):
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key and pergunta:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    contexto = df[['Título', 'Autor', 'Resumo']].head(40).to_string()
                    response = model.generate_content(f"Contexto: {contexto}\nPergunta: {pergunta}")
                    st.info(response.text)
                except Exception as e: st.error(f"Erro na API: {e}")

    with tab2:
        st.markdown("""
        <div style="background-color:#e2e3e5; padding:15px; border-radius:8px; margin-bottom:20px; color:#383d41;">
            <strong>Dica de Busca:</strong> Digite o título, nome do autor ou um tema. 
            O sistema filtrará automaticamente as obras abaixo.
        </div>
        """, unsafe_allow_html=True)
        
        busca = st.text_input("Procurar no acervo:", placeholder="Ex: Eisenstein, Roteiro, Hitchcock...")
        
        # Lógica de Filtro
        if busca:
            mask = df.apply(lambda r: busca.lower() in str(r.values).lower(), axis=1)
            resultados = df[mask]
        else:
            resultados = df.head(20)

        # --- O DESIGN DE 2 COLUNAS ---
        # Criamos as colunas fora do loop e distribuímos os cards
        cols = st.columns(2)
        
        for i, (index, row) in enumerate(resultados.iterrows()):
            # Lógica ABNT com s.d.
            autor_raw = str(row.get('Autor', '')).strip()
            titulo = str(row.get('Título', ''))
            editora = str(row.get('Editora', ''))
            data = str(row.get('Ano', '')).strip()
            if not data or data == "nan": data = "s.d."

            if autor_raw:
                partes = autor_raw.split()
                sobrenome = partes[-1].upper()
                nome_resto = " ".join(partes[:-1])
                citacao = f"{sobrenome}, {nome_resto}. **{titulo}**. {editora}, {data}."
            else:
                citacao = f"AUTOR DESCONHECIDO. **{titulo}**. {editora}, {data}."

            # Distribui entre coluna 0 e coluna 1
            with cols[i % 2]:
                st.markdown(f"""
                    <div class="book-card">
                        <h4 style="margin:0; color:#000;">{titulo}</h4>
                        <p style="color:blue; font-size:14px; margin-top:5px;">{autor_raw}</p>
                        <p style="font-size:13px; color:#444;">{row.get('Resumo', '')[:300]}...</p>
                        <div class="cdd-box">
                            📍 CDD {row.get('CDD', '---')} | Chamada: {row.get('Número de chamada', '---')}
                        </div>
                        <div class="abnt-text">Ref: {citacao}</div>
                    </div>
                """, unsafe_allow_html=True)

else:
    st.error("Arquivo biblioteca.xlsx não carregado.")

import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA - Acervo", layout="centered") # 'centered' garante uma coluna só

# Estilo para os cartões e layout
st.markdown("""
<style>
    .book-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #eee; margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .cdd-tag {
        background-color: #f1f3f4; padding: 8px 12px; border-radius: 6px;
        font-family: monospace; font-size: 13px; color: #444; border-left: 4px solid #000;
    }
    .abnt { font-size: 11px; color: #777; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- CARREGAR DADOS ---
@st.cache_data
def load_data():
    if not os.path.exists("biblioteca.xlsx"): return None
    df = pd.read_excel("biblioteca.xlsx")
    df.columns = df.columns.str.strip()
    return df.fillna("---")

df = load_data()

st.title("🎬 Cine.IA - Acervo de Cinema")

if df is not None:
    tab1, tab2 = st.tabs(["🔎 Procurar Livros", "🤖 Assistente de Produção"])

    with tab1:
        busca = st.text_input("Pesquisar no acervo:", placeholder="Título, autor ou assunto...")
        
        # Filtro: Se não houver busca, ele já abre com os primeiros livros
        if busca:
            mask = df.apply(lambda r: busca.lower() in str(r.values).lower(), axis=1)
            resultados = df[mask]
        else:
            resultados = df.head(15) # Já abre com 15 livros

        for _, row in resultados.iterrows():
            # Lógica da Citação ABNT
            autor_full = str(row.get('Autor', ''))
            if autor_full and autor_full != "---":
                partes = autor_full.split()
                sobrenome = partes[-1].upper()
                nome_resto = " ".join(partes[:-1])
                citacao_abnt = f"{sobrenome}, {nome_resto}. {row.get('Título')}. {row.get('Editora')}."
            else:
                citacao_abnt = f"AUTOR DESCONHECIDO. {row.get('Título')}."

            # Design de uma coluna (Container)
            st.markdown(f"""
                <div class="book-card">
                    <h3 style="margin-bottom:5px;">{row.get('Título')}</h3>
                    <p style="color:blue; margin-bottom:15px;">{row.get('Autor')} | {row.get('Editora')}</p>
                    <p style="font-size:14px; line-height:1.6;">{row.get('Resumo')}</p>
                    <div class="cdd-tag">
                        📍 <b>Localização:</b> CDD {row.get('CDD')} | <b>Cutter:</b> {row.get('Número de chamada')}
                    </div>
                    <div class="abnt"><b>Citação (ABNT):</b> {citacao_abnt}</div>
                </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.subheader("Assistente de Produção")
        pergunta = st.text_area("Como posso ajudar na sua pesquisa?")
        if st.button("Consultar IA"):
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key and pergunta:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    contexto = df[['Título', 'Autor', 'Resumo']].head(40).to_string()
                    response = model.generate_content(f"Acervo: {contexto}\nPergunta: {pergunta}")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")

# --- RESOLVENDO O PROBLEMA DO GITHUB NO TERMINAL ---
# Se o site do GitHub travar na ramificação, use estes comandos no terminal do VS Code:
# git checkout -B main
# git add .
# git commit -m "Versão final: Uma coluna e ABNT corrigida"
# git push origin main --force

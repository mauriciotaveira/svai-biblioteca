import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO DA PÁGINA (Interface Completa)
st.set_page_config(
    page_title="Acervo Cinema & Artes",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CONEXÃO COM A IA (Corrigida para gemini-1.5-flash)
api_status = False
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # Este é o modelo correto que substitui o antigo Pro e Flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        api_status = True
    except Exception:
        api_status = False

# 3. MOTOR DE DADOS (Lê Excel e prepara para busca V9)
@st.cache_data
def carregar_dados():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if arquivos:
        try:
            df = pd.read_excel(arquivos[0])
            # Remove espaços dos nomes das colunas
            df.columns = df.columns.astype(str).str.strip()
            return df, arquivos[0]
        except Exception as e:
            return None, f"Erro no Excel: {e}"
    return None, "Aguardando arquivo .xlsx..."

df, nome_arquivo = carregar_dados()

# 4. BARRA LATERAL (Visual Rico)
with st.sidebar:
    st.header("🗃️ Painel do Acervo")
    if df is not None:
        st.metric("📚 Total de Obras", len(df))
        st.write("---")
        # Filtro de Ano (Opcional, mas mantém a lista completa se não usar)
        colunas_lower = [c.lower() for c in df.columns]
        if 'ano' in colunas_lower:
            col_ano = df.columns[colunas_lower.index('ano')]
            anos_disponiveis = sorted(df[col_ano].dropna().astype(str).unique())
            ano_filtro = st.selectbox("Filtrar por Ano", ["Todos"] + anos_disponiveis)
        else:
            ano_filtro = "Todos"
    else:
        ano_filtro = "Todos"
    
    st.info(f"📁 Arquivo: {nome_arquivo}")
    st.caption("Sistema sVAI v.Final")

# 5. ÁREA PRINCIPAL
st.title("Acervo Cinema & Artes")

if df is not None:
    # --- MOTOR DE FILTRO (Lógica V9 + Filtro de Ano) ---
    df_filtrado = df.copy()
    
    # 1. Aplica filtro de ano se selecionado
    if ano_filtro != "Todos":
        col_ano = df.columns[[c.lower() for c in df.columns].index('ano')]
        df_filtrado = df_filtrado[df_filtrado[col_ano].astype(str) == ano_filtro]

    # Abas
    tab1, tab2 = st.tabs(["🔍 Pesquisa Geral", "🤖 Consultor IA"])

    # --- ABA 1: A PESQUISA QUE VOCÊ GOSTOU (MOTOR V9) ---
    with tab1:
        st.write("Digite qualquer termo: Título, Autor, Editora ou Assunto.")
        termo = st.text_input("Busca Rápida:", placeholder="Ex: Montagem, Eisenstein, 1998...")
        
        if termo:
            # ESTA É A MÁGICA DA VERSÃO 9:
            # Converte TODA a tabela para texto e busca o termo em qualquer lugar
            mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            resultado = df_filtrado[mask]
            
            st.success(f"Encontrados {len(resultado)} registros.")
            st.dataframe(resultado, use_container_width=True, hide_index=True)
        else:
            # Se não tem busca, mostra a tabela (filtrada pelo ano da sidebar)
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    # --- ABA 2: CONSULTOR IA (CORRIGIDO) ---
    with tab2:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        
        if not api_status:
            st.error("⚠️ Erro de API: Chave não configurada ou inválida.")
        else:
            pergunta = st.text_input("Qual a sua dúvida sobre o conteúdo dos livros?", key="ia_input")
            if st.button("Consultar IA"):
                if pergunta:
                    with st.spinner("Lendo o acervo..."):
                        try:
                            # Prepara amostra dos dados (Top 50 linhas do resultado da busca ou do total)
                            # Se o usuário fez uma busca na outra aba, a IA usa aquele contexto!
                            if termo and not resultado.empty:
                                contexto = resultado.head(50).to_string(index=False)
                                aviso = f"Baseado nos {len(resultado)} livros da sua busca:"
                            else:
                                contexto = df_filtrado.head(50).to_string(index=False)
                                aviso = "Baseado nos principais livros do acervo:"
                            
                            prompt = f"""
                            Você é um bibliotecário especialista. 
                            Responda à pergunta: '{pergunta}'
                            Use estritamente estes dados do acervo:
                            {contexto}
                            """
                            
                            response = model.generate_content(prompt)
                            st.markdown(f"**{aviso}**")
                            st.write(response.text)
                            
                        except Exception as e:
                            st.error(f"Erro técnico na IA: {e}")
                            st.caption("Tente novamente em alguns segundos.")

else:
    st.error("⚠️ Base de dados não carregada.")
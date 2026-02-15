import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO VISUAL (Estilo Versão 9 - Limpo)
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# 2. CARREGAMENTO DE DADOS (Excel)
@st.cache_data
def carregar_dados():
    # Procura qualquer arquivo Excel na pasta
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if arquivos:
        try:
            df = pd.read_excel(arquivos[0])
            # Garante que tudo seja texto para a busca não falhar
            df = df.astype(str)
            return df, arquivos[0]
        except Exception as e:
            return None, f"Erro no Excel: {e}"
    return None, "Nenhum arquivo .xlsx encontrado."

df, nome_arquivo = carregar_dados()

# 3. INTERFACE SIMPLIFICADA (Foco na Funcionalidade)
st.title("Acervo Cinema & Artes")

if df is not None:
    # Abas
    tab_busca, tab_ia = st.tabs(["🔍 Pesquisa Geral", "🤖 Consultor IA"])

    # --- MOTOR DE BUSCA (A Lógica da Versão 9) ---
    with tab_busca:
        st.write(f"Base de dados ativa: *{nome_arquivo}* ({len(df)} itens)")
        
        # O campo de busca simples e poderoso
        termo = st.text_input("O que você procura?", placeholder="Digite título, autor ou ano...")
        
        if termo:
            # O filtro que busca em TODAS as colunas ao mesmo tempo
            # case=False (ignora maiúsculas) | na=False (ignora vazios)
            mask = df.apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            resultado = df[mask]
            
            if not resultado.empty:
                st.success(f"{len(resultado)} registros encontrados.")
                st.dataframe(resultado, use_container_width=True, hide_index=True)
            else:
                st.warning("Nada encontrado com este termo.")
        else:
            # Se não digitar nada, mostra a tabela inteira
            st.dataframe(df, use_container_width=True, hide_index=True)

    # --- CONSULTOR IA (Isolado para não travar o site) ---
    with tab_ia:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        
        # Configuração da IA dentro da aba (para não quebrar a busca se falhar)
        chave_ok = False
        if "GOOGLE_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            chave_ok = True
        
        if not chave_ok:
            st.error("Chave API não encontrada.")
        else:
            pergunta = st.text_input("Qual sua dúvida sobre os livros?")
            if st.button("Consultar"):
                if pergunta:
                    with st.spinner("Analisando..."):
                        try:
                            # Usamos o modelo 'gemini-pro' (O Clássico Estável)
                            model = genai.GenerativeModel('gemini-pro')
                            
                            # Limitamos o contexto
                            contexto = df.head(50).to_string(index=False)
                            
                            response = model.generate_content(
                                f"Responda à pergunta: '{pergunta}'. Baseie-se nestes dados: {contexto}"
                            )
                            st.markdown(response.text)
                        except Exception as e:
                            st.error("A IA encontrou um erro técnico.")
                            st.code(f"Erro: {e}") # Mostra o erro técnico só aqui
else:
    st.error("⚠️ O arquivo Excel não foi carregado.")
    st.info("Verifique se 'biblioteca.xlsx' está no GitHub.")
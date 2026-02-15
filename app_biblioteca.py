import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide")

# 2. CARREGAMENTO INTELIGENTE (RESOLVE O PROBLEMA DOS "NAN")
@st.cache_data
def carregar_dados():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if arquivos:
        arquivo_atual = arquivos[0]
        try:
            # Lê o Excel sem assumir nada
            df = pd.read_excel(arquivo_atual, header=None)
            
            # --- FAXINA AUTOMÁTICA ---
            # Procura em qual linha estão os cabeçalhos reais (Título, Autor, etc.)
            linha_cabecalho = -1
            for i, row in df.head(10).iterrows():
                # Converte a linha para texto e procura palavras chave
                linha_texto = row.astype(str).str.lower().tolist()
                if 'título' in linha_texto or 'titulo' in linha_texto or 'autor' in linha_texto:
                    linha_cabecalho = i
                    break
            
            # Se achou o cabeçalho no meio do arquivo, recorta a tabela
            if linha_cabecalho > 0:
                df = pd.read_excel(arquivo_atual, header=linha_cabecalho)
            else:
                # Se não achou sujeira, lê normal (header na primeira linha)
                df = pd.read_excel(arquivo_atual)

            # Converte tudo para texto para garantir a busca (evita erros de número)
            df = df.astype(str)
            return df, arquivo_atual
            
        except Exception as e:
            return None, f"Erro ao ler Excel: {e}"
            
    return None, "Nenhum arquivo .xlsx encontrado."

df, nome_arquivo = carregar_dados()

# 3. INTERFACE LIMPA (ESTILO VERSÃO 9)
st.title("Acervo Cinema & Artes")

if df is not None:
    # Mostra qual arquivo está sendo lido
    st.caption(f"Base de dados: {nome_arquivo} | {len(df)} itens carregados corretamente.")

    tab_busca, tab_ia = st.tabs(["🔍 Pesquisa Geral", "🤖 Consultor IA"])

    # --- ABA 1: BUSCA GERAL ---
    with tab_busca:
        termo = st.text_input("Pesquisar no Acervo:", placeholder="Título, Autor, Assunto ou Ano...")
        
        if termo:
            # Remove linhas que sejam totalmente vazias ou 'nan'
            df_limpo = df.replace('nan', '', regex=False)
            
            # Busca em todas as colunas
            mask = df_limpo.apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            resultado = df_limpo[mask]
            
            if not resultado.empty:
                st.success(f"{len(resultado)} itens encontrados.")
                st.dataframe(resultado, use_container_width=True, hide_index=True)
            else:
                st.warning("Nada encontrado.")
        else:
            # Mostra a tabela completa (limpando os 'nan' visuais)
            st.dataframe(df.replace('nan', '', regex=False), use_container_width=True, hide_index=True)

    # --- ABA 2: CONSULTOR IA ---
    with tab_ia:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        
        chave_ok = False
        if "GOOGLE_API_KEY" in st.secrets:
            try:
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                chave_ok = True
            except:
                chave_ok = False
        
        if not chave_ok:
            st.error("⚠️ Chave API não configurada.")
        else:
            pergunta = st.text_input("Ex: Quais livros falam sobre montagem?")
            if st.button("Consultar IA"):
                if pergunta:
                    with st.spinner("Lendo livros..."):
                        try:
                            # Trocamos para o modelo FLASH (Mais rápido e atual)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            # Pega contexto (removemos linhas vazias para economizar tokens)
                            df_contexto = df.replace('nan', '', regex=False)
                            contexto = df_contexto.head(60).to_string(index=False)
                            
                            response = model.generate_content(
                                f"Aja como bibliotecário. Baseado nestes dados: {contexto}. Responda: {pergunta}"
                            )
                            st.info(response.text)
                        except Exception as e:
                            st.error(f"Erro na IA: {e}")
                            st.caption("Dica: Se o erro for 404, precisamos reiniciar o servidor (Reboot).")

else:
    st.error("⚠️ Erro ao carregar arquivo.")
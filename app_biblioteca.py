import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO DA PÁGINA (Layout Profissional)
st.set_page_config(
    page_title="Acervo Cinema & Artes",
    layout="wide",
    initial_sidebar_state="expanded"  # Barra lateral aberta por padrão
)

# 2. CONEXÃO COM A IA (Corrigido para gemini-pro)
api_status = False
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # Mudamos para o modelo PRO que é mais estável e evita o erro 404
        model = genai.GenerativeModel('gemini-pro')
        api_status = True
    except Exception:
        api_status = False

# 3. CARREGAMENTO DE DADOS (Blindado para Excel)
@st.cache_data
def carregar_dados():
    # Procura arquivos Excel na pasta
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if arquivos:
        try:
            df = pd.read_excel(arquivos[0])
            # Limpeza básica: remove espaços dos nomes das colunas
            df.columns = df.columns.astype(str).str.strip()
            return df, arquivos[0]
        except Exception as e:
            return None, f"Erro no Excel: {e}"
    return None, "Aguardando arquivo .xlsx..."

df, nome_arquivo = carregar_dados()

# 4. BARRA LATERAL (SIDEBAR) - Elementos que faltavam
with st.sidebar:
    st.header("🗃️ Painel de Controle")
    st.info(f"Base carregada: {nome_arquivo}")
    
    if df is not None:
        st.metric("Total de Itens", len(df))
        
        # Filtro rápido por Ano (se houver coluna Ano)
        colunas_lower = [c.lower() for c in df.columns]
        if 'ano' in colunas_lower:
            # Tenta encontrar a coluna correta de ano
            col_ano = df.columns[colunas_lower.index('ano')]
            anos = sorted(df[col_ano].dropna().unique())
            ano_selecionado = st.selectbox("Filtrar por Ano:", ["Todos"] + list(anos))
        else:
            ano_selecionado = "Todos"
            
    st.markdown("---")
    st.caption("Desenvolvido com sVAI © 2025")

# 5. ÁREA PRINCIPAL
st.title("📚 Acervo Cinema & Artes")

if df is not None:
    # Lógica de Filtro da Sidebar
    df_exibicao = df.copy()
    if ano_selecionado != "Todos":
        # Aplica o filtro se foi selecionado
        col_ano = df.columns[[c.lower() for c in df.columns].index('ano')]
        df_exibicao = df[df[col_ano] == ano_selecionado]

    # Abas Superiores
    tab1, tab2 = st.tabs(["🔍 Pesquisa Avançada", "🤖 Consultor IA"])

    # --- ABA DE PESQUISA ---
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            termo = st.text_input("🔎 Digite para buscar (Título, Autor, Assunto...):")
        with col2:
            st.write("") # Espaçamento
            st.write("") 
            limpar = st.button("Limpar Filtros")

        if termo and not limpar:
            # Busca inteligente em todo o dataframe
            mask = df_exibicao.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            resultado = df_exibicao[mask]
            
            if not resultado.empty:
                st.success(f"Encontrados {len(resultado)} registros para '{termo}'.")
                st.dataframe(resultado, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhum resultado encontrado.")
        else:
            # Mostra tudo se não tiver busca
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

    # --- ABA DA IA ---
    with tab2:
        st.markdown("### 🤖 Pergunte ao Bibliotecário")
        st.write("A IA analisa os livros listados na base e responde suas dúvidas.")
        
        if not api_status:
            st.error("⚠️ Erro de Conexão: Chave API inválida ou não configurada.")
        else:
            col_perg, col_bt = st.columns([4, 1])
            with col_perg:
                pergunta = st.text_input("Ex: 'Quais livros falam sobre montagem?'", key="input_ia")
            with col_bt:
                st.write("")
                st.write("")
                enviar = st.button("Enviar 🚀")

            if enviar and pergunta:
                with st.spinner("Lendo o acervo..."):
                    try:
                        # Prepara os dados (Top 60 linhas para caber na memória rápida)
                        dados_contexto = df_exibicao.head(60).to_string(index=False)
                        
                        prompt = f"""
                        Você é um bibliotecário especialista em Cinema.
                        Use os dados abaixo para responder à pergunta do usuário.
                        Se a resposta não estiver nos dados, diga que não encontrou no acervo.
                        
                        DADOS DO ACERVO:
                        {dados_contexto}
                        
                        PERGUNTA DO USUÁRIO:
                        {pergunta}
                        """
                        
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.markdown(response.text)
                        
                    except Exception as e:
                        st.error(f"A IA encontrou um problema técnico: {e}")
                        st.caption("Dica: Tente uma pergunta mais simples.")

else:
    st.error("⚠️ Base de dados não carregada.")
    st.info("Verifique se o arquivo 'biblioteca.xlsx' está no GitHub.")
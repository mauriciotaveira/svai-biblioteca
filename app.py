import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Cine.IA - Biblioteca", layout="wide")

# Título do site
st.title("🎬 Cine.IA - Acervo de Cinema")
st.markdown("---")

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    # O robô salvou as colunas novas, então lemos o arquivo atualizado
    df = pd.read_excel("biblioteca.xlsx")
    # Limpar espaços extras nos nomes das colunas para evitar erros
    df.columns = df.columns.str.strip()
    return df

try:
    df = carregar_dados()

    # --- BARRA LATERAL (Filtros) ---
    st.sidebar.header("🔍 Filtros")
    categorias = ["Todos"] + sorted(df['Categoria'].dropna().unique().tolist())
    categoria_selecionada = st.sidebar.selectbox("Escolha uma Categoria", categorias)

    busca = st.sidebar.text_input("Buscar por título ou autor")

    # --- LÓGICA DE FILTRO ---
    dados_filtrados = df.copy()

    if categoria_selecionada != "Todos":
        dados_filtrados = dados_filtrados[dados_filtrados['Categoria'] == categoria_selecionada]

    if busca:
        dados_filtrados = dados_filtrados[
            dados_filtrados['Título'].str.contains(busca, case=False, na=False) |
            dados_filtrados['Autor'].str.contains(busca, case=False, na=False)
        ]

    # --- EXIBIÇÃO DOS CARTÕES ---
    st.subheader(f"📚 Livros Encontrados ({len(dados_filtrados)})")

    for index, row in dados_filtrados.iterrows():
        with st.container():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                # Espaço para ícone ou imagem
                st.write("📖")
                
            with col2:
                st.subheader(f"{row['Título']}")
                st.write(f"**Autor:** {row['Autor']} | **Editora:** {row['Editora']}")
                
                # --- O BLOCO DA CATALOGAÇÃO (A parte que o robô fez!) ---
                # Usamos st.info para dar um destaque visual cinza/azul
                cdd = row.get('CDD', '---')
                cutter = row.get('Número de chamada', '---')
                st.info(f"📍 **Catalogação:** CDD {cdd} | Cutter: {cutter}")

                # --- RESUMO ---
                with st.expander("Ver Resumo"):
                    resumo = row.get('Resumo', 'Resumo não disponível.')
                    st.write(resumo)
                
                # --- CITAÇÃO ABNT ---
                # Pequena automação para gerar a citação na hora
                sobrenome = str(row['Autor']).split()[-1].upper() if pd.notna(row['Autor']) else ""
                citacao = f"{sobrenome}, {row['Autor']}. {row['Título']}. {row['Editora']}."
                st.caption(f"Citação (ABNT): {citacao}")
                
            st.markdown("---")

except Exception as e:
    st.error(f"Erro ao carregar a biblioteca: {e}")
    st.info("Verifique se o arquivo 'biblioteca.xlsx' está na pasta e se o formato está correto.")

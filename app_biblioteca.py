import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Acervo Cinema & Artes", layout="wide", initial_sidebar_state="expanded")

# 2. FUNÇÃO DE LIMPEZA DE DADOS (A SALVAÇÃO DA TABELA)
@st.cache_data
def carregar_dados_inteligente():
    arquivos = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not arquivos:
        return None, "Nenhum Excel encontrado."
    
    arquivo = arquivos[0]
    try:
        # A. Lê o arquivo sem cabeçalho para inspecionar
        df_bruto = pd.read_excel(arquivo, header=None)
        
        # B. Procura em qual linha está a palavra "Autor" ou "Título"
        indice_cabecalho = -1
        for i, row in df_bruto.head(15).iterrows():
            linha_texto = row.astype(str).str.lower().tolist()
            # Verifica se alguma palavra chave está na linha
            if any(x in linha_texto for x in ['autor', 'título', 'titulo', 'editora']):
                indice_cabecalho = i
                break
        
        # C. Recarrega o arquivo usando a linha correta como cabeçalho
        if indice_cabecalho >= 0:
            df = pd.read_excel(arquivo, header=indice_cabecalho)
        else:
            df = pd.read_excel(arquivo) # Tenta normal se não achar

        # D. Limpeza Final (Remove colunas vazias e converte para texto)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.astype(str)
        # Remove linhas onde tudo é 'nan'
        df = df.replace('nan', '')
        
        return df, arquivo

    except Exception as e:
        return None, f"Erro Crítico: {e}"

df, nome_arquivo = carregar_dados_inteligente()

# 3. BARRA LATERAL (Agora vai funcionar porque achamos o cabeçalho)
with st.sidebar:
    st.header("🗂️ Filtros")
    if df is not None:
        # Tenta achar a coluna de Categoria independentemente de maiúscula/minúscula
        col_cat = next((c for c in df.columns if c.lower() == 'categoria'), None)
        
        if col_cat:
            opcoes = sorted(list(set(df[col_cat].unique())))
            # Remove vazios da lista
            opcoes = [x for x in opcoes if x != '' and x != 'nan']
            filtro_cat = st.selectbox("Categoria:", ["Todas"] + opcoes)
        else:
            st.warning("Coluna 'Categoria' não identificada.")
            filtro_cat = "Todas"
            
        st.metric("Obras no Acervo", len(df))

# 4. ÁREA PRINCIPAL
st.title("Acervo Cinema & Artes")

if df is not None:
    # Aplica o filtro
    if filtro_cat != "Todas" and 'col_cat' in locals() and col_cat:
        df_exibicao = df[df[col_cat] == filtro_cat]
    else:
        df_exibicao = df

    tab1, tab2 = st.tabs(["🔍 Pesquisa", "🤖 Consultor IA"])

    with tab1:
        termo = st.text_input("Busca Rápida:", placeholder="Digite qualquer termo...")
        if termo:
            mask = df_exibicao.apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            st.dataframe(df_exibicao[mask], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

    with tab2:
        st.write("### Pergunte ao Bibliotecário")
        
        # Tenta configurar a IA
        ia_ativa = False
        if "GOOGLE_API_KEY" in st.secrets:
            try:
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                # Forçamos o modelo mais compatível
                model = genai.GenerativeModel('gemini-1.5-flash')
                ia_ativa = True
            except:
                pass

        if not ia_ativa:
            st.error("Chave API não configurada.")
        else:
            pergunta = st.text_input("Dúvida:")
            if st.button("Enviar"):
                if pergunta:
                    try:
                        contexto = df_exibicao.head(40).to_string()
                        resp = model.generate_content(f"Dados: {contexto}. Pergunta: {pergunta}")
                        st.info(resp.text)
                    except Exception as e:
                        st.error(f"Erro IA: {e}")
                        st.caption("Se este erro persistir, DELETE o app no Streamlit e crie novamente.")
else:
    st.error(f"Erro ao ler dados: {nome_arquivo}")
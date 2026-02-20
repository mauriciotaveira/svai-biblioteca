with tab1:
        st.markdown("""
        <div class="guide-box">
            <strong>Como navegar no Assistente:</strong><br>
            • Deseja uma análise profunda baseada no acervo?<br>
            • Digite sua pergunta sobre teoria, técnica ou história do cinema.<br>
            • O sistema redigirá um texto técnico e fundamentado utilizando os livros disponíveis.
        </div>
        """, unsafe_allow_html=True)
        
        pergunta = st.text_area("Sua consulta técnica:", height=150)
        
        if st.button("Obter Resposta Técnica"):
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key and pergunta:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash') 
                    
                    # --- O TRUQUE DO FILTRO INTELIGENTE ---
                    # 1. Pega as palavras da sua pergunta com mais de 3 letras
                    palavras_chave = [p.lower() for p in pergunta.split() if len(p) > 3]
                    
                    # 2. Busca no Excel inteiro apenas os livros que tenham essas palavras
                    if palavras_chave:
                        mask = df.apply(lambda r: any(p in str(r.values).lower() for p in palavras_chave), axis=1)
                        df_relevante = df[mask]
                    else:
                        df_relevante = df.head(0)
                    
                    # 3. Se achou poucos, completa com os primeiros para garantir contexto
                    if len(df_relevante) < 5:
                        df_relevante = pd.concat([df_relevante, df.head(15)]).drop_duplicates()
                    
                    # 4. Limita a 20 obras altamente focadas (Para não estourar a cota gratuita)
                    colunas_disponiveis = [c for c in ['Título', 'Autor', 'Resumo', 'Editora', 'Ano'] if c in df.columns]
                    contexto = df_relevante[colunas_disponiveis].head(20).to_string()
                    
                    # --- O PROMPT MESTRE ---
                    prompt_final = f"""
                    Você é um especialista em cinema. Responda à pergunta do usuário baseado APENAS no acervo fornecido abaixo.
                    
                    DIRETRIZES:
                    1. Escreva um texto longo, fluido, dissertativo e profundo. Discorra sobre o tema conectando as ideias dos autores presentes no acervo.
                    2. NÃO faça listas superficiais. Construa parágrafos encadeados.
                    3. TOM: Seja elegante e direto.
                    4. REFERÊNCIAS ABNT: É OBRIGATÓRIO que o último elemento da sua resposta seja uma seção chamada "Referências Citadas", listando todas as obras que você usou no texto no formato ABNT (SOBRENOME, Nome. Título. Editora, Ano.). Se o ano não existir, use s.d.
                    
                    Acervo selecionado para esta pergunta: 
                    {contexto}
                    
                    Pergunta: {pergunta}
                    """
                    
                    with st.spinner("Mapeando acervo e redigindo ensaio..."):
                        response = model.generate_content(prompt_final)
                        st.markdown(f'<div class="ai-response-box">{response.text}</div>', unsafe_allow_html=True)
                except Exception as e: 
                    st.error(f"Erro na conexão com a API: {e}")

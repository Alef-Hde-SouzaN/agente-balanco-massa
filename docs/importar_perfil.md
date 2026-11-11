# Importar o perfil do agente
1. Subir API e Open WebUI com `docker compose --profile chat up --build -d`.
2. Criar conta local no Open WebUI.
3. Configurar a conexão de modelos Groq: https://api.groq.com/openai/v1, Bearer com chave PRÓPRIA. Não incluir chaves no repositório. O plano gratuito possui cotas e pode mudar.
4. Cadastrar External Tools OpenAPI com URL http://api:8000, schema openapi.json, autenticação Nenhum e ID EXATO balanco_massa. Salvar janela e página.
5. Espaço de Trabalho > Modelos > Import: selecionar config/analista-balanco-massa.json.
6. Editar o perfil importado e conferir modelo base openai/gpt-oss-20b, ferramenta Balanço de Massa marcada e Function Calling Padrão. Manter privado. Se o modelo não estiver disponível na conta, selecionar outro compatível e repetir as avaliações.
7. Abrir nova conversa com Analista de Balanço de Massa. Testar consulta da 21579005: ENCERRADA, 2026-10, bloqueada frente a 2026-11.

O JSON é um perfil com instruções, não pesos de um modelo nem credencial. Removidos do export: user, user_id e timestamps; incluíam e-mail, identificador e avatar pessoais. Nenhuma chave de API encontrada no export inspecionado. O vínculo server:balanco_massa exige cadastrar esse servidor separadamente; importar o perfil não configura automaticamente modelo/provedor/servidor.

## Configuração validada em 10/11/2026
- Open WebUI v0.6.34; modelo base `openai/gpt-oss-20b` via Groq.
- Function Calling: **Padrão**; Stream Chat Response: **Padrão**. O export atual omite esses parâmetros, herdando os padrões. Conferir após importar.
- Administração > Configurações > Interface > modelo de tarefas para modelos externos: selecionar diretamente **GPT OSS 20B**, não o perfil Analista. Esta configuração é global e não acompanha o JSON do perfil.
- O modo Padrão faz uma seleção prévia de ferramentas; pode não encadear consultas como Native. As ferramentas retornam regras e elegibilidade necessárias para a decisão, e a simulação inclui a análise.
- Native apresentou respostas vazias nos testes locais. Padrão sem modelo auxiliar explícito apresentou erro de seleção e conflito de ferramenta. Após os ajustes, os casos 21579001, 21579007 e 21579005 tiveram respostas corretas nas execuções observadas. Isso não comprova confiabilidade universal.
- Limite de tokens da conta Groq interrompeu uma execução. Aguardar e tentar novamente; cotas variam por conta/provedor. Desativar sugestões, títulos e tags automáticos se for necessário reduzir chamadas auxiliares.
- A API não envia dados à Groq sozinha: o chat envia ao provedor as informações retornadas pelas ferramentas. Usar somente dados fictícios nesta entrega.
- O arquivo temporário compose.debug.yaml e os logs de diagnóstico não fazem parte da entrega. Depois de concluir a investigação, voltar ao serviço normal com `docker compose --profile chat up -d open-webui`; fazer login novamente se a sessão expirar.

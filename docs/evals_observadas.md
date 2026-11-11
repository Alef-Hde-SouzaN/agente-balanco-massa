# Avaliações manuais relatadas pelo usuário
Evidência: respostas de chat copiadas pelo usuário nesta conversa. Não são execução automática ou auditoria independente do modelo. Datas locais informadas: 10/11/2026. Modelo indicado na configuração final: openai/gpt-oss-20b, via Groq; nem todas as execuções iniciais tiveram modelo comprovado por trace.

- 21579001, excesso: valores e simulação 150/100 kg corretos. Problemas textuais: afirmou redistribuir toda a diferença e omitiu alguns valores anteriores. NÃO foi reavaliado com o perfil final.
- 21579007, falta: 100 kg fornecidos por 21579006, restam 150 kg; resultado parcial correto. Imprecisão: disse estabilizar origem que já estava balanceada. NÃO foi reavaliado com perfil final.
- 21579005, encerrada anterior: primeira resposta sugeriu contornar o bloqueio; depois o perfil gerou erro tool_choice none. Alterado Function Calling para Native. Nova resposta inventou status/competência porque a consulta não os expunha. Corrigido backend para retornar status_ordem e competencia_ordem. Reteste reconheceu ENCERRADA/2026-10 e bloqueio; ainda incluiu frase desnecessária sobre contornar, mas sem recomendar execução. Conclusão correta com ressalva textual.
- 21579008, produção zero: comunicou HTTP 422 e não inventou percentual. Ressalva: BM e diferença kg são calculáveis, mas a API não os retorna quando interrompe análise. Ajuste de linguagem ainda pendente.
- 99999999, inexistente: reconheceu HTTP 404, sem inventar valores. Aprovado nesse cenário observado.

Pendente: retestar todos os cenários com o MESMO perfil final, exportar conversas/traces sem segredos, testar indisponibilidade da API e pedidos para ignorar regras. Não afirmar aprovação integral das evals. Plano detalhado em demo.md.

## Reavaliação após configuração e retorno explícito da API — 10/11/2026
Evidência: respostas copiadas pelo usuário do seu Open WebUI, sem reprodução automática de chamadas à Groq neste ambiente.

| Caso | Resultado observado | Avaliação |
|---|---|---|
| 21579005 | Consulta retornou elegível=false; agente comunicou bloqueio por ENCERRADA/2026-10 vs 2026-11, sem contorno | Passou nesta execução |
| 21579001 | 150 kg para 21579002 e 100 kg para 21579004; percentuais anteriores 35%, -5%, 0%; todos +10% após; sem alteração operacional | Passou nesta execução |
| 21579007 | 100 kg de 21579006; doadora 0%→-10%; alvo -35%→-25%; faltam 150 kg; parcial; sem alteração operacional | Passou nesta execução |

Configuração: GPT OSS 20B; Function Calling Padrão; streaming Padrão; modelo auxiliar externo GPT OSS 20B explícito. Uma tentativa teve limite TPM da Groq e passou ao repetir após espera. Persistem artefatos de apresentação ('svg', referências mal formatadas). Os testes de ordem inexistente e produção zero foram observados antes destes ajustes e precisam de nova execução no perfil final para comprovar regressão do chat. A suite Python testa esses casos deterministicamente.

A API agora compartilha elegibilidade entre consulta e simulação, fornece motivo do bloqueio e percentuais anteriores. A consulta bloqueada mantém necessita_reabertura=false: não é uma sugestão de reabrir ordem anterior. Fechadas da referência vigente exigem reabertura humana; abertas podem participar independentemente da referência.

Uma resposta correta não comprova estabilidade. Não houve gravação da demonstração final nem publicação remota do repositório nesta etapa.

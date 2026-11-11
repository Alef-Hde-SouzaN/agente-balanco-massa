# Fonte de conhecimento — regras v1.0
Dados exclusivamente fictícios, inspirados na convenção solicitada por Alef. Não representam tabelas ou customização universal do SAP.

BM = consumo líquido kg - produção líquida kg.
Diferença kg = BM - perda apontada líquida kg.
Diferença % = diferença kg / produção líquida kg * 100.
Faixa inclusiva: -10% a +10%. Produção líquida <= zero impede cálculo.

Movimentos: 101 produção (+), 102 estorno (-); 261 consumo (+), 262 estorno (-); 531 perda apontada (+), 532 estorno (-). O tratamento de 531 como perda segue o processo informado, não uma afirmação de semântica universal SAP.
Material: 1xxxxxxxxxxx produção, 2xxxxxxxxxxx perda, 3xxxxxxxxxxx consumo.
Quantidade armazenada positiva; sinal vem do tipo de movimento. Conversão por material/unidade (KG ou MIL) antes de somar. Na amostra, 1 MIL = 20 kg; é fator fictício específico, não regra geral.

Realocar apenas o mesmo material de consumo já presente nas duas ordens. Não exigir mesma máquina/produto. Retirar no máximo o saldo líquido disponível do material. Aceitar várias origens/destinos. Objetivo: entrar na tolerância, não zerar o desvio. Ordens candidatas devem terminar dentro da tolerância; alvo pode ficar parcialmente ajustado se não houver capacidade suficiente.
Ordens abertas elegíveis; encerradas só da competência vigente configurada. Encerradas exigem reabertura humana, nunca executada pelo agente.
A competência do cenário é 2026-11, fixa por configuração para reprodução, não a data do computador. Alterar BM_COMPETENCIA para uso em outra competência.

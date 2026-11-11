from datetime import date
from decimal import Decimal as D
import os


Z = D("0")


class RegraError(ValueError):
    pass


def carregar(con):
    ordens = {
        r["numero"]: dict(
            r,
            producao=Z,
            perda=Z,
            materiais={},
            evidencias=[],
        )
        for r in con.execute("SELECT * FROM ordens ORDER BY numero")
    }

    query = """
        SELECT
            m.*,
            t.categoria,
            t.sinal,
            c.kg_por_unidade,
            a.categoria AS categoria_material
        FROM movimentos m
        JOIN tipos_movimento t ON t.codigo = m.tipo
        JOIN materiais a ON a.codigo = m.material
        JOIN conversoes c
            ON c.material = m.material
            AND c.unidade = m.unidade
        ORDER BY m.documento
    """

    for r in con.execute(query):
        if r["categoria"] != r["categoria_material"]:
            raise RegraError(
                "Categoria do material incompatível com movimento"
            )

        quantidade = D(r["quantidade"])
        fator = D(r["kg_por_unidade"])

        if (
            not quantidade.is_finite()
            or not fator.is_finite()
            or quantidade < 0
            or fator <= 0
        ):
            raise RegraError("Quantidade ou conversão inválida")

        kg = quantidade * fator * r["sinal"]
        ordem = ordens[r["ordem"]]

        if r["categoria"] == "CONSUMO":
            material = r["material"]
            ordem["materiais"][material] = (
                ordem["materiais"].get(material, Z) + kg
            )
        else:
            campo = (
                "producao"
                if r["categoria"] == "PRODUCAO"
                else "perda"
            )
            ordem[campo] += kg

        ordem["evidencias"].append(
            dict(r, quantidade_kg_liquida=str(kg))
        )

    for ordem in ordens.values():
        if ordem["perda"] < 0 or any(
            quantidade < 0
            for quantidade in ordem["materiais"].values()
        ):
            raise RegraError(
                "Estornos excedem os apontamentos disponíveis"
            )

    return ordens


def limites(ordem):
    minimo = ordem["perda"] + D("0.9") * ordem["producao"]
    maximo = ordem["perda"] + D("1.1") * ordem["producao"]
    return minimo, maximo


def verificar_elegibilidade(ordem, competencia):
    status = ordem["status"]
    competencia_ordem = ordem["competencia"]

    aberta = status == "ABERTA"
    encerrada_vigente = (
        status == "ENCERRADA"
        and competencia_ordem == competencia
    )
    permitida = aberta or encerrada_vigente

    if aberta:
        motivo = "Ordem aberta; pode participar da simulação."

    elif encerrada_vigente:
        motivo = (
            "Ordem encerrada da competência vigente; pode participar "
            "da simulação, mas a execução exige reabertura humana."
        )

    elif status == "ENCERRADA":
        motivo = (
            f"Ordem encerrada da competência {competencia_ordem}, "
            f"fora da competência vigente {competencia}. "
            "Não pode participar da realocação. "
            "Não reabrir, alterar a competência ou aguardar mudança "
            "de mês para contornar esse bloqueio."
        )

    else:
        motivo = (
            f"Status {status} não autorizado para realocação."
        )

    return {
        "status_ordem": status,
        "competencia_ordem": competencia_ordem,
        "competencia_vigente": competencia,
        "elegivel_para_realocacao": permitida,
        "necessita_reabertura": encerrada_vigente,
        "motivo_elegibilidade": motivo,
    }


def elegivel(ordem, competencia):
    return verificar_elegibilidade(
        ordem, competencia
    )["elegivel_para_realocacao"]


def resumo(ordem, consumo=None):
    if consumo is None:
        consumo = sum(ordem["materiais"].values(), Z)

    producao = ordem["producao"]
    perda = ordem["perda"]

    if producao <= 0:
        raise RegraError(
            "Produção líquida precisa ser maior que zero"
        )

    minimo, maximo = limites(ordem)

    bm = consumo - producao
    diferenca = bm - perda
    percentual = diferenca / producao * D("100")

    if consumo < minimo:
        classificacao = "FALTA_CONSUMO"
    elif consumo > maximo:
        classificacao = "EXCESSO_CONSUMO"
    else:
        classificacao = "BALANCEADA"

    return {
        "ordem": ordem["numero"],
        "maquina": ordem["maquina"],
        "setor": ordem["setor"],
        "consumo_kg": str(consumo),
        "producao_kg": str(producao),
        "perda_apontada_kg": str(perda),
        "bm_kg": str(bm),
        "diferenca_kg": str(diferenca),
        "diferenca_percentual": str(percentual),
        "classificacao": classificacao,
    }


def analisar(con, codigo, competencia=None):
    if competencia is None:
        competencia = os.getenv(
            "BM_COMPETENCIA",
            date.today().strftime("%Y-%m"),
        )

    base = carregar(con)

    if codigo not in base:
        raise KeyError(codigo)

    ordem = base[codigo]

    return {
        **resumo(ordem),
        **verificar_elegibilidade(ordem, competencia),
        "materiais": {
            material: str(quantidade)
            for material, quantidade in ordem["materiais"].items()
        },
        "evidencias": ordem["evidencias"],
        "fonte": "SQLite: movimentos + conversoes + tipos_movimento",
    }


def simular(con, codigo, competencia):
    base = carregar(con)

    if codigo not in base:
        raise KeyError(codigo)

    alvo = base[codigo]

    inicial = {
        **resumo(alvo),
        **verificar_elegibilidade(alvo, competencia),
    }

    if not inicial["elegivel_para_realocacao"]:
        return {
            "resultado": "REALOCACAO_BLOQUEADA",
            "analise": inicial,
            "motivo_bloqueio": inicial["motivo_elegibilidade"],
            "movimentos": [],
            "ordens_apos_simulacao": [],
            "dados_operacionais_alterados": False,
        }

    totais = {
        numero: sum(ordem["materiais"].values(), Z)
        for numero, ordem in base.items()
    }
    antes = totais.copy()

    minimo_alvo, maximo_alvo = limites(alvo)
    falta = totais[codigo] < minimo_alvo

    restante = max(
        Z,
        minimo_alvo - totais[codigo],
        totais[codigo] - maximo_alvo,
    )

    movimentos = []

    candidatos = sorted(
        base.items(),
        key=lambda item: (
            item[1]["status"] == "ENCERRADA",
            item[0],
        ),
    )

    for numero, ordem in candidatos:
        if restante == 0:
            break

        if (
            numero == codigo
            or ordem["producao"] <= 0
            or not elegivel(ordem, competencia)
        ):
            continue

        minimo, maximo = limites(ordem)

        if falta:
            origem, destino = numero, codigo
            capacidade = totais[numero] - minimo
            regularizar = max(Z, totais[numero] - maximo)
        else:
            origem, destino = codigo, numero
            capacidade = maximo - totais[numero]
            regularizar = max(Z, minimo - totais[numero])

        materiais_comuns = sorted(
            set(base[origem]["materiais"])
            & set(base[destino]["materiais"])
        )

        disponivel = sum(
            (
                base[origem]["materiais"][material]
                for material in materiais_comuns
            ),
            Z,
        )

        quantidade = min(
            restante,
            capacidade,
            disponivel,
        )

        if quantidade <= 0 or quantidade < regularizar:
            continue

        pendente = quantidade

        for material in materiais_comuns:
            if pendente == 0:
                break

            transferir = min(
                pendente,
                base[origem]["materiais"][material],
            )

            if transferir <= 0:
                continue

            base[origem]["materiais"][material] -= transferir
            base[destino]["materiais"][material] += transferir

            totais[origem] -= transferir
            totais[destino] += transferir

            movimentos.append(
                {
                    "ordem_origem": origem,
                    "ordem_destino": destino,
                    "material": material,
                    "quantidade_kg": str(transferir),
                }
            )

            pendente -= transferir

        restante -= quantidade

    envolvidos = {codigo}

    for movimento in movimentos:
        envolvidos.add(movimento["ordem_origem"])
        envolvidos.add(movimento["ordem_destino"])

    depois = []

    for numero in sorted(envolvidos):
        ordem = base[numero]
        resumo_antes = resumo(ordem, antes[numero])
        resumo_depois = resumo(ordem, totais[numero])

        depois.append(
            {
                **resumo_depois,
                **verificar_elegibilidade(ordem, competencia),
                "consumo_antes_kg": str(antes[numero]),
                "diferenca_antes_kg": resumo_antes["diferenca_kg"],
                "diferenca_antes_percentual": (
                    resumo_antes["diferenca_percentual"]
                ),
                "classificacao_antes": resumo_antes["classificacao"],
            }
        )

    if inicial["classificacao"] == "BALANCEADA":
        resultado = "SEM_NECESSIDADE_DE_AJUSTE"
    elif restante == 0:
        resultado = "SOLUCAO_COMPLETA"
    elif movimentos:
        resultado = "SOLUCAO_PARCIAL"
    else:
        resultado = "SEM_COMBINACAO_ENCONTRADA"

    return {
        "analise": inicial,
        "resultado": resultado,
        "movimentos": movimentos,
        "ordens_apos_simulacao": depois,
        "ajuste_ainda_necessario_kg": str(restante),
        "dados_operacionais_alterados": False,
        "limitacao": (
            "Busca gulosa; não garante solução ótima ou todas "
            "as combinações. Valores decimais em texto preservam "
            "precisão. Solução completa significa entrar na "
            "tolerância, não necessariamente zerar a diferença."
        ),
    }
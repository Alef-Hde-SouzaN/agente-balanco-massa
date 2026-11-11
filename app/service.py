from decimal import Decimal as D
import json
Z = D('0')

class RegraError(ValueError):
    pass

def carregar(con):
    ordens = {r['numero']: dict(r, producao=Z, perda=Z, materiais={}, evidencias=[]) for r in con.execute('SELECT * FROM ordens ORDER BY numero')}
    query = '''SELECT m.*, t.categoria, t.sinal, c.kg_por_unidade, a.categoria AS categoria_material
    FROM movimentos m JOIN tipos_movimento t ON t.codigo=m.tipo
    JOIN materiais a ON a.codigo=m.material
    JOIN conversoes c ON c.material=m.material AND c.unidade=m.unidade ORDER BY m.documento'''
    for r in con.execute(query):
        if r['categoria'] != r['categoria_material']:
            raise RegraError('Categoria do material incompatível com movimento')
        qtd, fator = D(r['quantidade']), D(r['kg_por_unidade'])
        if not qtd.is_finite() or not fator.is_finite() or qtd < 0 or fator <= 0:
            raise RegraError('Quantidade ou conversão inválida')
        kg = qtd * fator * r['sinal']
        o = ordens[r['ordem']]
        if r['categoria'] == 'CONSUMO':
            o['materiais'][r['material']] = o['materiais'].get(r['material'], Z) + kg
        else:
            campo = 'producao' if r['categoria'] == 'PRODUCAO' else 'perda'
            o[campo] += kg
        o['evidencias'].append(dict(r, quantidade_kg_liquida=str(kg)))
    for o in ordens.values():
        if o['perda'] < 0 or any(v < 0 for v in o['materiais'].values()):
            raise RegraError('Estornos excedem os apontamentos disponíveis')
    return ordens

def limites(o):
    return o['perda'] + D('.9')*o['producao'], o['perda'] + D('1.1')*o['producao']

def elegivel(o, competencia):
    return o['status'] == 'ABERTA' or o['competencia'] == competencia

def resumo(o, consumo=None):
    c = sum(o['materiais'].values(), Z) if consumo is None else consumo
    p, perda = o['producao'], o['perda']
    if p <= 0:
        raise RegraError('Produção líquida precisa ser maior que zero')
    lo, hi = limites(o)
    return dict(ordem=o['numero'], maquina=o['maquina'], setor=o['setor'], consumo_kg=str(c), producao_kg=str(p), perda_apontada_kg=str(perda), bm_kg=str(c-p), diferenca_kg=str(c-p-perda), diferenca_percentual=str((c-p-perda)/p*100), classificacao='FALTA_CONSUMO' if c<lo else 'EXCESSO_CONSUMO' if c>hi else 'BALANCEADA')

def analisar(con, codigo):
    base = carregar(con)
    if codigo not in base:
        raise KeyError(codigo)
    o = base[codigo]
    return dict(resumo(o), materiais={m:str(v) for m,v in o['materiais'].items()}, evidencias=o['evidencias'], fonte='SQLite: movimentos + conversoes + tipos_movimento')

def simular(con, codigo, competencia):
    base = carregar(con)
    if codigo not in base:
        raise KeyError(codigo)
    alvo = base[codigo]
    inicial = resumo(alvo)
    if not elegivel(alvo, competencia):
        return dict(resultado='REALOCACAO_BLOQUEADA', analise=inicial, movimentos=[])
    totais = {k:sum(o['materiais'].values(), Z) for k,o in base.items()}
    antes = totais.copy()
    lo, hi = limites(alvo)
    falta = totais[codigo] < lo
    restante = max(Z, lo-totais[codigo], totais[codigo]-hi)
    movimentos = []
    for k,o in sorted(base.items(), key=lambda item:(item[1]['status']=='ENCERRADA',item[0])):
        if restante == 0:
            break
        if k==codigo or o['producao']<=0 or not elegivel(o, competencia):
            continue
        minimo,maximo = limites(o)
        origem,destino = (k,codigo) if falta else (codigo,k)
        comuns = sorted(set(base[origem]['materiais']) & set(base[destino]['materiais']))
        capacidade = totais[k]-minimo if falta else maximo-totais[k]
        regularizar = max(Z,totais[k]-maximo if falta else minimo-totais[k])
        disponivel = sum((base[origem]['materiais'][m] for m in comuns), Z)
        q = min(restante,capacidade,disponivel)
        if q<=0 or q<regularizar:
            continue
        pendente=q
        for m in comuns:
            transferir=min(pendente,base[origem]['materiais'][m])
            if transferir<=0:
                continue
            base[origem]['materiais'][m]-=transferir
            base[destino]['materiais'][m]+=transferir
            totais[origem]-=transferir
            totais[destino]+=transferir
            movimentos.append(dict(ordem_origem=origem,ordem_destino=destino,material=m,quantidade_kg=str(transferir)))
            pendente-=transferir
        restante-=q
    envolvidos={codigo}|{m[chave] for m in movimentos for chave in ('ordem_origem','ordem_destino')}
    depois=[dict(resumo(base[k],totais[k]),consumo_antes_kg=str(antes[k]),necessita_reabertura=base[k]['status']=='ENCERRADA') for k in sorted(envolvidos)]
    return dict(analise=inicial,resultado='SEM_NECESSIDADE_DE_AJUSTE' if inicial['classificacao']=='BALANCEADA' else 'SOLUCAO_COMPLETA' if restante==0 else 'SOLUCAO_PARCIAL' if movimentos else 'SEM_COMBINACAO_ENCONTRADA',movimentos=movimentos,ordens_apos_simulacao=depois,ajuste_ainda_necessario_kg=str(restante),dados_operacionais_alterados=False,limitacao='Busca gulosa; não garante solução ótima ou todas as combinações. Valores decimais em texto preservam precisão.')

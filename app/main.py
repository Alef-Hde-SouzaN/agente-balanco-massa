from contextlib import asynccontextmanager
from datetime import date
import json
import logging
import os
import re
from fastapi import FastAPI, HTTPException
from .db import conectar, inicializar
from .service import analisar, simular, RegraError
log = logging.getLogger('uvicorn.error')

@asynccontextmanager
async def lifespan(app):
    inicializar()
    yield

app = FastAPI(title='Balanço de Massa — ferramentas do agente', version='1.0.0', lifespan=lifespan)

def executar(nome, codigo, func):
    if not re.fullmatch(r'[0-9]{8}', codigo):
        raise HTTPException(422,'Ordem deve conter oito dígitos numéricos')
    try:
        with conectar() as con:
            resultado=func(con)
            con.execute('INSERT INTO auditoria(ferramenta,ordem,resultado) VALUES(?,?,?)',(nome,codigo,json.dumps(resultado,ensure_ascii=False)))
        log.info('tool=%s ordem=%s status=ok',nome,codigo)
        return resultado
    except KeyError:
        raise HTTPException(404,'Ordem não encontrada na base de demonstração')
    except RegraError as erro:
        raise HTTPException(422,str(erro))

@app.get('/health', include_in_schema=False)
def health():
    with conectar() as con:
        con.execute('SELECT 1').fetchone()
    return {'status':'ok'}

@app.get('/ordens',operation_id='listar_ordens')
def listar_ordens():
    """Lista exclusivamente ordens da base fictícia autorizada."""
    with conectar() as con:
        return [dict(r) for r in con.execute('SELECT * FROM ordens ORDER BY numero')]

@app.get('/regras',operation_id='consultar_regras')
def regras():
    """Fonte de conhecimento: fórmula, tolerância e limites de realocação."""
    return {'fonte':'docs/regras.md','versao':'1.0','formula':'(consumo_kg - producao_kg - perda_kg) / producao_kg * 100','tolerancia_inclusiva':[-10,10],'competencia_vigente':os.getenv('BM_COMPETENCIA',date.today().strftime('%Y-%m')),'regras':['Mesmo material consumido; máquinas e produtos podem diferir','Ordens encerradas apenas da competência vigente; reabertura humana','Nunca alterar movimentos; apenas simulação','Produção líquida zero ou negativa impede cálculo','Estornos subtraídos por categoria; conversões específicas por material']}

@app.get('/ordens/{codigo}/balanco',operation_id='consultar_balanco')
def balanco(codigo:str):
    """Calcula balanço em kg, incluindo estornos e evidências por documento."""
    return executar('consultar_balanco',codigo,lambda con:analisar(con,codigo))

@app.get('/ordens/{codigo}/simulacao',operation_id='simular_realocacao')
def simulacao(codigo:str):
    """Simula consumo do mesmo material entre ordens; não executa lançamentos."""
    competencia=os.getenv('BM_COMPETENCIA',date.today().strftime('%Y-%m'))
    return executar('simular_realocacao',codigo,lambda con:simular(con,codigo,competencia))

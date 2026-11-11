import tempfile
import unittest
from pathlib import Path
from decimal import Decimal as D
from app.db import inicializar, conectar
from app.service import analisar, simular, RegraError

class BalancoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/'test.sqlite3')
        inicializar(self.path)
        self.con=conectar(self.path)
    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()
    def test_estornos_conversao(self):
        r=analisar(self.con,'21579001')
        self.assertEqual(D(r['consumo_kg']),1400)
        self.assertEqual(D(r['producao_kg']),1000)
        self.assertEqual(D(r['perda_apontada_kg']),50)
        self.assertEqual(D(r['diferenca_percentual']),35)
        self.assertEqual(len(r['evidencias']),6)
    def test_excesso_multiplas_ordens_sem_mutacao(self):
        antes=list(self.con.execute('SELECT * FROM movimentos'))
        r=simular(self.con,'21579001','2026-11')
        self.assertEqual(r['resultado'],'SOLUCAO_COMPLETA')
        self.assertEqual([D(m['quantidade_kg']) for m in r['movimentos']],[150,100])
        self.assertEqual(sum(D(m['quantidade_kg']) for m in r['movimentos']),250)
        self.assertTrue(all(o['classificacao']=='BALANCEADA' for o in r['ordens_apos_simulacao']))
        self.assertEqual(antes,list(self.con.execute('SELECT * FROM movimentos')))
    def test_falta_parcial_material(self):
        r=simular(self.con,'21579007','2026-11')
        self.assertEqual(r['resultado'],'SOLUCAO_PARCIAL')
        self.assertTrue(all(m['material']=='300000000002' for m in r['movimentos']))
        self.assertEqual(D(r['ajuste_ainda_necessario_kg']),150)
    def test_encerrada_anterior(self):
        self.assertEqual(simular(self.con,'21579005','2026-11')['resultado'],'REALOCACAO_BLOQUEADA')
    def test_limites_inclusivos(self):
        self.assertEqual(analisar(self.con,'21579003')['classificacao'],'BALANCEADA')
        self.con.execute("UPDATE movimentos SET quantidade='48.5' WHERE ordem='21579003' AND tipo='261'")
        self.assertEqual(D(analisar(self.con,'21579003')['diferenca_percentual']),-10)
        self.assertEqual(analisar(self.con,'21579003')['classificacao'],'BALANCEADA')
    def test_status_competencia_explicitos(self):
        r=analisar(self.con,'21579005')
        self.assertEqual(r['status_ordem'],'ENCERRADA')
        self.assertEqual(r['competencia_ordem'],'2026-10')
    def test_elegibilidade_explicita_consulta_e_simulacao(self):
        r = analisar(self.con, '21579005', '2026-11')
        self.assertFalse(r['elegivel_para_realocacao'])
        self.assertFalse(r['necessita_reabertura'])
        self.assertEqual(r['competencia_vigente'], '2026-11')
        bloqueio = simular(self.con, '21579005', '2026-11')
        self.assertEqual(bloqueio['motivo_bloqueio'], r['motivo_elegibilidade'])
        self.assertFalse(bloqueio['dados_operacionais_alterados'])
        self.assertEqual(bloqueio['movimentos'], [])

    def test_aberta_anterior_e_encerrada_vigente(self):
        self.con.execute("UPDATE ordens SET competencia='2026-10' WHERE numero='21579001'")
        r = analisar(self.con, '21579001', '2026-11')
        self.assertTrue(r['elegivel_para_realocacao'])
        self.assertFalse(r['necessita_reabertura'])
        r = analisar(self.con, '21579003', '2026-11')
        self.assertTrue(r['elegivel_para_realocacao'])
        self.assertTrue(r['necessita_reabertura'])

    def test_percentuais_antes_e_depois_e_conservacao(self):
        for codigo, esperado in [('21579001', {'21579001': 35, '21579002': -5, '21579004': 0}),
                                 ('21579007', {'21579006': 0, '21579007': -35})]:
            r = simular(self.con, codigo, '2026-11')
            ordens = r['ordens_apos_simulacao']
            self.assertEqual(sum(D(o['consumo_antes_kg']) for o in ordens),
                             sum(D(o['consumo_kg']) for o in ordens))
            for o in ordens:
                self.assertEqual(D(o['diferenca_antes_percentual']), esperado[o['ordem']])

    def test_zero_producao(self):
        with self.assertRaises(RegraError): analisar(self.con,'21579008')
    def test_inexistente(self):
        with self.assertRaises(KeyError): analisar(self.con,'99999999')
    def test_reabertura_vigente(self):
        self.con.execute("UPDATE ordens SET status='ENCERRADA' WHERE numero='21579002'")
        r=simular(self.con,'21579001','2026-11')
        self.assertTrue(any(o['necessita_reabertura'] for o in r['ordens_apos_simulacao']))
    def test_seed_idempotente(self):
        inicializar(self.path)
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM movimentos').fetchone()[0],48)
    def test_estorno_excessivo(self):
        self.con.execute("UPDATE movimentos SET quantidade='9999' WHERE ordem='21579001' AND tipo='262'")
        with self.assertRaises(RegraError): analisar(self.con,'21579001')

if __name__=='__main__': unittest.main()

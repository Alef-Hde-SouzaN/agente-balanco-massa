PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS materiais(codigo TEXT PRIMARY KEY CHECK(length(codigo)=12 AND codigo NOT GLOB '*[^0-9]*'), descricao TEXT NOT NULL, categoria TEXT NOT NULL CHECK(categoria IN ('PRODUCAO','PERDA','CONSUMO')));
CREATE TABLE IF NOT EXISTS conversoes(material TEXT REFERENCES materiais(codigo), unidade TEXT, kg_por_unidade TEXT NOT NULL, PRIMARY KEY(material,unidade));
CREATE TABLE IF NOT EXISTS ordens(numero TEXT PRIMARY KEY CHECK(length(numero)=8 AND numero NOT GLOB '*[^0-9]*'), status TEXT CHECK(status IN ('ABERTA','ENCERRADA')), competencia TEXT NOT NULL, maquina TEXT, setor TEXT);
CREATE TABLE IF NOT EXISTS tipos_movimento(codigo TEXT PRIMARY KEY, categoria TEXT, sinal INTEGER CHECK(sinal IN (-1,1)));
INSERT OR IGNORE INTO tipos_movimento VALUES('101','PRODUCAO',1),('102','PRODUCAO',-1),('261','CONSUMO',1),('262','CONSUMO',-1),('531','PERDA',1),('532','PERDA',-1);
CREATE TABLE IF NOT EXISTS movimentos(documento TEXT PRIMARY KEY, ordem TEXT REFERENCES ordens(numero), material TEXT REFERENCES materiais(codigo), tipo TEXT REFERENCES tipos_movimento(codigo), quantidade TEXT NOT NULL, unidade TEXT NOT NULL, data TEXT NOT NULL, FOREIGN KEY(material,unidade) REFERENCES conversoes(material,unidade));
CREATE TABLE IF NOT EXISTS auditoria(id INTEGER PRIMARY KEY, instante TEXT DEFAULT CURRENT_TIMESTAMP, ferramenta TEXT, ordem TEXT, resultado TEXT);

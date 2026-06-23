#!/usr/bin/env python3
# =====================================================================
#  MercadoKwanza — Migração CLIENTE + VENDA → MongoDB
#  Base de Dados II | ISPTEC | Lab #02 — Parte 2, Problema 3 — Cenário B
#
#  Cenário B (Grupo 6): Migra CLIENTE com lista de vendas embutidas.
#  Compara tempo de consulta (top 10 clientes com mais compras)
#  entre MySQL e MongoDB.
#
#  Pré-requisito: pip install mysql-connector-python pymongo
#  Execução:      python scripts/migracao_clientes.py
# =====================================================================

import mysql.connector
import pymongo
import time

print('=' * 60)
print('  MercadoKwanza — Migração CLIENTE + VENDA → MongoDB')
print('=' * 60)

mysql_conn = mysql.connector.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='kwanza2024',
    database='mercadokwanza'
)
mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
db  = mongo_client['mercadokwanza']
col = db['clientes']

# Limpar colecção anterior
col.drop()
print('[MongoDB] Colecção "clientes" limpa.')

cur = mysql_conn.cursor(dictionary=True)

# Carregar clientes
print('[MySQL]   A carregar clientes...')
cur.execute('SELECT id, nome, nif, provincia_id, telefone, activo FROM CLIENTE')
clientes = cur.fetchall()

docs = []
for c in clientes:
    cur.execute(
        'SELECT id, loja_id, data_venda, total '
        'FROM VENDA WHERE cliente_id = %s',
        (c['id'],)
    )
    vendas = cur.fetchall()
    for v in vendas:
        v['data_venda'] = str(v['data_venda'])
        v['total']      = float(v['total'])
    c['vendas'] = vendas
    c['activo'] = int(c['activo'])
    docs.append(c)

print(f'[MySQL]   {len(docs)} clientes carregados com vendas. A inserir no MongoDB...')
t0 = time.time()
col.insert_many(docs)
t_migracao = time.time() - t0
print(f'[MongoDB] {len(docs)} documentos inseridos em {t_migracao:.2f}s.')

# Criar índices
col.create_index('provincia_id')
col.create_index('nome')
print('[MongoDB] Índices criados.')

# ── Comparação: top 10 clientes com mais compras ─────────────────────
print('\n' + '-' * 60)
print('  COMPARAÇÃO — Top 10 clientes com mais compras')
print('-' * 60)

# MongoDB
t0 = time.time()
top_mongo = list(col.aggregate([
    { '$project': { 'nome': 1, 'n_vendas': { '$size': '$vendas' } } },
    { '$sort':    { 'n_vendas': -1 } },
    { '$limit':   10 }
]))
t_mongo = (time.time() - t0) * 1000

print(f'\n[MongoDB] Tempo: {t_mongo:.2f} ms')
print(f'          Top cliente: {top_mongo[0]["nome"]} ({top_mongo[0]["n_vendas"]} compras)')

# MySQL
cur.execute('SET profiling = 1')
t0 = time.time()
cur.execute(
    'SELECT SQL_NO_CACHE c.id, c.nome, COUNT(v.id) AS n_vendas '
    'FROM CLIENTE c '
    'LEFT JOIN VENDA v ON v.cliente_id = c.id '
    'GROUP BY c.id, c.nome '
    'ORDER BY n_vendas DESC '
    'LIMIT 10'
)
top_mysql = cur.fetchall()
t_mysql = (time.time() - t0) * 1000
cur.execute('SET profiling = 0')

print(f'\n[MySQL]   Tempo: {t_mysql:.2f} ms')
print(f'          Top cliente: {top_mysql[0]["nome"]} ({top_mysql[0]["n_vendas"]} compras)')

print(f'\n  Mais rápido: {"MongoDB" if t_mongo < t_mysql else "MySQL"} '
      f'(diferença: {abs(t_mongo - t_mysql):.2f} ms)')

cur.close()
mysql_conn.close()
mongo_client.close()
print('\n[Sistema] Migração e comparação concluídas.\n')

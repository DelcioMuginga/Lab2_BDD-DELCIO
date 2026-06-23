#!/usr/bin/env python3
# =====================================================================
#  MercadoKwanza — Migração MySQL → MongoDB
#  Base de Dados II | ISPTEC | Lab #02 — Parte 2, Problema 3
#
#  Cenário A (Grupo 5): Migra VENDA + ITEM_VENDA como documentos embutidos.
#  Compara tempo de agregação (total por loja) entre MySQL e MongoDB.
#
#  Pré-requisito: pip install mysql-connector-python pymongo
#  Execução:      python scripts/migracao.py
# =====================================================================

import mysql.connector
import pymongo
import time
import datetime

# ── Ligações ─────────────────────────────────────────────────────────
print('=' * 60)
print('  MercadoKwanza — Migração VENDA + ITEM_VENDA → MongoDB')
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
col = db['vendas']

# ── Limpar colecção anterior ─────────────────────────────────────────
col.drop()
print('[MongoDB] Colecção "vendas" limpa.')

# ── Migração ─────────────────────────────────────────────────────────
cur = mysql_conn.cursor(dictionary=True)

print('[MySQL]   A carregar vendas...')
t_inicio = time.time()

cur.execute('SELECT id, loja_id, cliente_id, data_venda, total FROM VENDA')
vendas = cur.fetchall()

docs = []
for v in vendas:
    cur.execute(
        'SELECT produto_id, qtd, preco_unit, desconto '
        'FROM ITEM_VENDA WHERE venda_id = %s',
        (v['id'],)
    )
    v['itens']      = cur.fetchall()
    v['data_venda'] = str(v['data_venda'])
    v['total']      = float(v['total'])
    docs.append(v)

print(f'[MySQL]   {len(docs)} vendas carregadas com itens. A inserir no MongoDB...')
col.insert_many(docs)

t_migracao = time.time() - t_inicio
print(f'[MongoDB] {len(docs)} documentos inseridos em {t_migracao:.2f}s.')

# ── Criar índice para melhorar agregação ─────────────────────────────
col.create_index('loja_id')
print('[MongoDB] Índice criado em loja_id.')

# ── Comparação de desempenho: Total de vendas por loja ──────────────
print('\n' + '-' * 60)
print('  COMPARAÇÃO DE DESEMPENHO — Total de vendas por loja')
print('-' * 60)

# MongoDB:
t0 = time.time()
resultado_mongo = list(col.aggregate([
    { '$group': { '_id': '$loja_id', 'total': { '$sum': '$total' }, 'count': { '$sum': 1 } } },
    { '$sort': { 'total': -1 } }
]))
t_mongo = (time.time() - t0) * 1000

print(f'\n[MongoDB] Tempo de agregação: {t_mongo:.2f} ms')
print(f'          Número de lojas no resultado: {len(resultado_mongo)}')
if resultado_mongo:
    top = resultado_mongo[0]
    print(f'          Loja com maior total: loja_id={top["_id"]} — {top["total"]:,.2f} Kz')

# MySQL:
cur.execute('SET profiling = 1')
t0 = time.time()
cur.execute(
    'SELECT SQL_NO_CACHE loja_id, SUM(total) AS total, COUNT(*) AS n_vendas '
    'FROM VENDA GROUP BY loja_id ORDER BY total DESC'
)
resultado_mysql = cur.fetchall()
t_mysql = (time.time() - t0) * 1000
cur.execute('SET profiling = 0')

print(f'\n[MySQL]   Tempo de agregação: {t_mysql:.2f} ms')
print(f'          Número de lojas no resultado: {len(resultado_mysql)}')
if resultado_mysql:
    top = resultado_mysql[0]
    print(f'          Loja com maior total: loja_id={top["loja_id"]} — {float(top["total"]):,.2f} Kz')

print(f'\n  Mais rápido: {"MongoDB" if t_mongo < t_mysql else "MySQL"} '
      f'(diferença: {abs(t_mongo - t_mysql):.2f} ms)')

# ── Encerrar ─────────────────────────────────────────────────────────
cur.close()
mysql_conn.close()
mongo_client.close()
print('\n[Sistema] Migração e comparação concluídas.\n')

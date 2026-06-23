#!/usr/bin/env python3
# =====================================================================
#  MercadoKwanza — PARTE 2 | PROBLEMA 3 — CENÁRIO A (Grupo 7)
#  SQL vs NoSQL + Teorema CAP
#
#  Cenário A: Migrar VENDA + ITEM_VENDA para MongoDB como documentos
#  embutidos. Comparar tempo de agregação (total por loja) entre
#  MySQL e MongoDB.
#
#  Execução:
#    python scripts/problema3_sql_vs_nosql.py
#
#  Pré-requisito: pip install mysql-connector-python pymongo
# =====================================================================

import mysql.connector
import pymongo
import time
import json

SEPARADOR = '=' * 62


def separador(titulo: str) -> None:
    print(f'\n{SEPARADOR}')
    print(f'  {titulo}')
    print(SEPARADOR)


def log(sistema: str, msg: str, resultado: str) -> None:
    print(f'  [{sistema:8}] {msg:45} -> {resultado}')


# ════════════════════════════════════════════════════════════════════
# LIGAÇÕES
# ════════════════════════════════════════════════════════════════════
separador('MercadoKwanza — Problema 3, Cenário A: SQL vs NoSQL')

mysql_conn = mysql.connector.connect(
    host='127.0.0.1', port=3306,
    user='root', password='kwanza2024',
    database='mercadokwanza'
)
mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
db  = mongo_client['mercadokwanza']
col = db['vendas']

log('MySQL',   'Ligação ao nó Luanda (porta 3306)', 'OK')
log('MongoDB', 'Ligação ao mongo-kwanza (porta 27017)', 'OK')


# ════════════════════════════════════════════════════════════════════
# PASSO 1 — MIGRAÇÃO MySQL → MongoDB
# Cada venda torna-se um documento JSON com os seus itens embutidos
# ════════════════════════════════════════════════════════════════════
separador('PASSO 1 — Migração VENDA + ITEM_VENDA → MongoDB')

col.drop()
log('MongoDB', 'Colecção "vendas" anterior apagada', 'OK')

cur = mysql_conn.cursor(dictionary=True)

print('\n  A carregar vendas do MySQL...')
t_mig_inicio = time.time()

cur.execute('SELECT id, loja_id, cliente_id, data_venda, total FROM VENDA')
vendas = cur.fetchall()
log('MySQL', f'Vendas carregadas', f'{len(vendas)} documentos')

docs = []
for v in vendas:
    cur.execute(
        'SELECT produto_id, qtd, preco_unit, desconto '
        'FROM ITEM_VENDA WHERE venda_id = %s',
        (v['id'],)
    )
    itens = cur.fetchall()
    doc = {
        'venda_id':    v['id'],
        'loja_id':     v['loja_id'],
        'cliente_id':  v['cliente_id'],
        'data_venda':  str(v['data_venda']),
        'total':       float(v['total']),
        'itens':       [
            {
                'produto_id': i['produto_id'],
                'qtd':        i['qtd'],
                'preco_unit': float(i['preco_unit']),
                'desconto':   float(i['desconto'])
            }
            for i in itens
        ]
    }
    docs.append(doc)

# Inserção em lote (muito mais rápido que inserir um a um)
col.insert_many(docs, ordered=False)
t_mig_fim = time.time()

log('MongoDB', f'Documentos inseridos com itens embutidos',
    f'{len(docs)} docs em {t_mig_fim - t_mig_inicio:.2f}s')

# Criar índices para melhorar a performance das agregações
col.create_index('loja_id')
col.create_index('cliente_id')
log('MongoDB', 'Índices criados (loja_id, cliente_id)', 'OK')

# Mostrar um documento de exemplo
exemplo = col.find_one({}, {'_id': 0})
print(f'\n  Exemplo de documento MongoDB:')
print(f'  {json.dumps(exemplo, indent=4, ensure_ascii=False, default=str)[:500]}...')


# ════════════════════════════════════════════════════════════════════
# PASSO 2 — COMPARAÇÃO DE DESEMPENHO: Total de vendas por loja
# ════════════════════════════════════════════════════════════════════
separador('PASSO 2 — Comparação: Total de Vendas por Loja')

# ── MongoDB ──────────────────────────────────────────────────────────
# Aquecimento (evita penalizar a primeira query por cache fria)
list(col.aggregate([{'$group': {'_id': '$loja_id', 'total': {'$sum': '$total'}}}]))

t0 = time.time()
resultado_mongo = list(col.aggregate([
    {'$group': {
        '_id':    '$loja_id',
        'total':  {'$sum': '$total'},
        'count':  {'$sum': 1}
    }},
    {'$sort': {'total': -1}}
]))
t_mongo_ms = (time.time() - t0) * 1000

print(f'\n  [MongoDB] Pipeline de agregação executada')
print(f'            Tempo:          {t_mongo_ms:.2f} ms')
print(f'            Lojas no resultado: {len(resultado_mongo)}')
if resultado_mongo:
    top = resultado_mongo[0]
    print(f'            Loja com maior total: loja_id={top["_id"]} — {top["total"]:,.2f} Kz ({top["count"]} vendas)')

# ── MySQL ─────────────────────────────────────────────────────────────
# Desactivar cache de queries para medição justa
cur.execute('SET profiling = 1')

t0 = time.time()
cur.execute(
    'SELECT SQL_NO_CACHE loja_id, '
    'SUM(total) AS total_vendas, '
    'COUNT(*) AS n_vendas '
    'FROM VENDA '
    'GROUP BY loja_id '
    'ORDER BY total_vendas DESC'
)
resultado_mysql = cur.fetchall()
t_mysql_ms = (time.time() - t0) * 1000

cur.execute('SHOW PROFILES')
profiles = cur.fetchall()
cur.execute('SET profiling = 0')

print(f'\n  [MySQL]   Query GROUP BY executada')
print(f'            Tempo (Python):  {t_mysql_ms:.2f} ms')
if profiles:
    ultimo = profiles[-1]
    # SHOW PROFILES retorna: Query_ID, Duration, Query
    print(f'            Tempo (PROFILES): {float(ultimo[1])*1000:.2f} ms')
print(f'            Lojas no resultado: {len(resultado_mysql)}')
if resultado_mysql:
    top = resultado_mysql[0]
    print(f'            Loja com maior total: loja_id={top["loja_id"]} — {float(top["total_vendas"]):,.2f} Kz ({top["n_vendas"]} vendas)')

# ── Tabela comparativa ────────────────────────────────────────────────
print(f'\n  {"─"*50}')
print(f'  RESUMO DA COMPARAÇÃO')
print(f'  {"─"*50}')
print(f'  MongoDB:  {t_mongo_ms:7.2f} ms')
print(f'  MySQL:    {t_mysql_ms:7.2f} ms')
vencedor = "MongoDB" if t_mongo_ms < t_mysql_ms else "MySQL"
diff = abs(t_mongo_ms - t_mysql_ms)
print(f'  Mais rápido: {vencedor} (diferença: {diff:.2f} ms)')
print(f'  {"─"*50}')


# ════════════════════════════════════════════════════════════════════
# PASSO 3 — ANÁLISE DO TEOREMA CAP
# ════════════════════════════════════════════════════════════════════
separador('PASSO 3 — Posicionamento no Teorema CAP')

cap = {
    'MySQL Master-Slave': {
        'Consistência (C)':            'FORTE no Master; EVENTUAL nos Slaves (lag de replicação)',
        'Disponibilidade (A)':         'Alta para leituras (Slaves); limitada para escritas (só Master)',
        'Tolerância Partições (P)':    'Parcial — Slaves continuam a responder se Master cair',
        'Posição CAP':                 'CP — prefere consistência a disponibilidade em caso de partição',
        'Modelo ACID/BASE':            'ACID — transações com garantias fortes',
        'Melhor para':                 'Operações transaccionais: vendas, stock, pagamentos',
    },
    'MongoDB Standalone': {
        'Consistência (C)':            'FORTE num único nó (todas as leituras vêem o último write)',
        'Disponibilidade (A)':         'Alta — responde sempre enquanto o nó estiver activo',
        'Tolerância Partições (P)':    'N/A (nó único) — com replica set torna-se CP ou AP configurável',
        'Posição CAP':                 'CA (nó único) / CP com replica set (writeConcern majority)',
        'Modelo ACID/BASE':            'ACID a nível de documento; BASE a nível de colecção',
        'Melhor para':                 'Relatórios analíticos, schema variável, dados semi-estruturados',
    }
}

for sistema, props in cap.items():
    print(f'\n  ┌─ {sistema} {"─"*(45-len(sistema))}┐')
    for k, v in props.items():
        print(f'  │  {k:<30}: {v}')
    print(f'  └{"─"*52}┘')


# ════════════════════════════════════════════════════════════════════
# PASSO 4 — VERIFICAÇÃO DE CONSISTÊNCIA DOS DADOS
# Os resultados de MySQL e MongoDB devem ser idênticos
# ════════════════════════════════════════════════════════════════════
separador('PASSO 4 — Verificação de Consistência MySQL ↔ MongoDB')

# Construir dicionários {loja_id: total} para comparação
dict_mongo = {r['_id']: round(r['total'], 2) for r in resultado_mongo}
dict_mysql = {r['loja_id']: round(float(r['total_vendas']), 2) for r in resultado_mysql}

inconsistencias = 0
for loja_id, total_mysql in dict_mysql.items():
    total_mongo = dict_mongo.get(loja_id, None)
    if total_mongo is None or abs(total_mysql - total_mongo) > 0.01:
        inconsistencias += 1
        print(f'  [AVISO] Loja {loja_id}: MySQL={total_mysql} vs MongoDB={total_mongo}')

if inconsistencias == 0:
    print(f'  ✓ Todos os {len(dict_mysql)} registos são consistentes entre MySQL e MongoDB.')
else:
    print(f'  ✗ {inconsistencias} inconsistências detectadas — rever migração.')

# ── Encerrar ──────────────────────────────────────────────────────────
separador('Execução concluída')
cur.close()
mysql_conn.close()
mongo_client.close()
print('  Ligações MySQL e MongoDB encerradas.\n')

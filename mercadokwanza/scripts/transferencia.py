#!/usr/bin/env python3
# =====================================================================
#  MercadoKwanza — Transferência de Stock entre Províncias
#  Base de Dados II | ISPTEC | Lab #02 — Parte 2, Problema 2 — Cenário B
#
#  Cenário: Transferir 30 unidades de uma loja de Huambo para Benguela.
#  - Se stock em Huambo >= 30: decrementa Huambo, incrementa Benguela.
#  - Se stock insuficiente: ROLLBACK em ambos os nós.
#
#  Pré-requisito: pip install mysql-connector-python
#  Execução:      python scripts/transferencia.py
# =====================================================================

import mysql.connector
import datetime

# ── Parâmetros da transferência ──────────────────────────────────────
PRODUTO_ID      = 10   # Produto a transferir
LOJA_HUAMBO     = 11   # Loja em Huambo (provincia_id = 3)
LOJA_BENGUELA   = 6    # Loja destino em Benguela (provincia_id = 2)
QUANTIDADE      = 30   # Unidades a transferir

# ── Função de log ────────────────────────────────────────────────────
def log(no: str, operacao: str, resultado: str) -> None:
    ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]
    print(f'[{ts}] [{no:12}] {operacao:45} -> {resultado}')

# ── Função de conexão ────────────────────────────────────────────────
def conectar(porta: int):
    return mysql.connector.connect(
        host='127.0.0.1',
        port=porta,
        user='root',
        password='kwanza2024',
        database='mercadokwanza',
        autocommit=False
    )

print('=' * 60)
print('  MercadoKwanza — Transferência de Stock entre Províncias')
print(f'  Produto: {PRODUTO_ID} | Quantidade: {QUANTIDADE}')
print(f'  Origem:  Huambo  (loja {LOJA_HUAMBO})')
print(f'  Destino: Benguela (loja {LOJA_BENGUELA})')
print('=' * 60)

no_huambo   = None
no_benguela = None

try:
    no_huambo   = conectar(3308)   # Huambo na porta 3308
    no_benguela = conectar(3307)   # Benguela na porta 3307
    cur_h = no_huambo.cursor()
    cur_b = no_benguela.cursor()
    log('Sistema', 'Ligações estabelecidas (Huambo + Benguela)', 'OK')

    # ── Verificar stock em Huambo (com bloqueio) ─────────────────────
    cur_h.execute(
        'SELECT quantidade FROM STOCK '
        'WHERE produto_id = %s AND loja_id = %s FOR UPDATE',
        (PRODUTO_ID, LOJA_HUAMBO)
    )
    row = cur_h.fetchone()

    if row is None:
        raise Exception(f'Produto {PRODUTO_ID} não existe na loja {LOJA_HUAMBO} (Huambo)')

    stock_huambo = row[0]
    log('Huambo', f'Stock actual produto {PRODUTO_ID}', f'{stock_huambo} unidades')

    if stock_huambo < QUANTIDADE:
        raise Exception(
            f'Stock insuficiente em Huambo: disponível={stock_huambo}, pedido={QUANTIDADE}'
        )

    # ── Decrementar stock em Huambo ───────────────────────────────────
    cur_h.execute(
        'UPDATE STOCK SET quantidade = quantidade - %s, atualizado_em = NOW() '
        'WHERE produto_id = %s AND loja_id = %s',
        (QUANTIDADE, PRODUTO_ID, LOJA_HUAMBO)
    )
    log('Huambo', f'UPDATE STOCK -={QUANTIDADE}', 'OK')

    # ── Verificar e incrementar stock em Benguela ─────────────────────
    cur_b.execute(
        'SELECT quantidade FROM STOCK '
        'WHERE produto_id = %s AND loja_id = %s FOR UPDATE',
        (PRODUTO_ID, LOJA_BENGUELA)
    )
    row_b = cur_b.fetchone()
    stock_benguela_antes = row_b[0] if row_b else 0
    log('Benguela', f'Stock actual produto {PRODUTO_ID}', f'{stock_benguela_antes} unidades')

    if row_b:
        cur_b.execute(
            'UPDATE STOCK SET quantidade = quantidade + %s, atualizado_em = NOW() '
            'WHERE produto_id = %s AND loja_id = %s',
            (QUANTIDADE, PRODUTO_ID, LOJA_BENGUELA)
        )
    else:
        cur_b.execute(
            'INSERT INTO STOCK (produto_id, loja_id, quantidade, atualizado_em) '
            'VALUES (%s, %s, %s, NOW())',
            (PRODUTO_ID, LOJA_BENGUELA, QUANTIDADE)
        )
    log('Benguela', f'UPDATE/INSERT STOCK +={QUANTIDADE}', 'OK')

    # ── COMMIT nos dois nós ───────────────────────────────────────────
    no_huambo.commit()
    log('Huambo', 'COMMIT', 'executado')
    no_benguela.commit()
    log('Benguela', 'COMMIT', 'executado')

    print(f'\n✓ Transferência concluída com sucesso!')
    print(f'  Huambo:   {stock_huambo} → {stock_huambo - QUANTIDADE} unidades')
    print(f'  Benguela: {stock_benguela_antes} → {stock_benguela_antes + QUANTIDADE} unidades')

except Exception as e:
    log('Sistema', 'ERRO detectado', str(e))
    if no_huambo:
        no_huambo.rollback()
        log('Huambo', 'ROLLBACK', 'executado')
    if no_benguela:
        no_benguela.rollback()
        log('Benguela', 'ROLLBACK', 'executado')
    print(f'\n✗ Transferência cancelada. Motivo: {e}')

finally:
    if no_huambo:
        no_huambo.close()
    if no_benguela:
        no_benguela.close()
    print('  Ligações encerradas.\n')

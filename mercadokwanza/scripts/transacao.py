#!/usr/bin/env python3
# =====================================================================
#  MercadoKwanza — Transação Distribuída (Two-Phase Commit Simplificado)
#  Base de Dados II | ISPTEC | Lab #02 — Fase 4
#
#  Cenário: cliente de Luanda compra produto cujo stock está em Benguela.
#  - Nó Benguela: decrementa stock (UPDATE STOCK)
#  - Nó Luanda:   regista a venda (INSERT VENDA + ITEM_VENDA)
#  - Se qualquer operação falhar: ROLLBACK em ambos os nós.
#
#  Pré-requisito: pip install mysql-connector-python
#  Execução:      python scripts/transacao.py
# =====================================================================

import mysql.connector
import datetime

# ── Parâmetros da transação ──────────────────────────────────────────
PRODUTO_ID    = 5     # Produto a vender
LOJA_BENGUELA = 6     # Loja em Benguela (provincia_id = 2)
LOJA_LUANDA   = 1     # Loja em Luanda   (provincia_id = 1)
CLIENTE_ID    = 42    # Cliente de Luanda
QUANTIDADE    = 10    # Unidades a vender
PRECO_UNIT    = 1500  # Preço unitário (Kz)

# ── Função de log com timestamp ──────────────────────────────────────
def log(no: str, operacao: str, resultado: str) -> None:
    ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]
    print(f'[{ts}] [{no:12}] {operacao:40} -> {resultado}')

# ── Função de conexão ────────────────────────────────────────────────
def conectar(porta: int):
    conn = mysql.connector.connect(
        host='127.0.0.1',
        port=porta,
        user='root',
        password='kwanza2024',
        database='mercadokwanza',
        autocommit=False   # IMPORTANTE: desactivar autocommit para controlo manual
    )
    return conn

# ── Início da transação distribuída ─────────────────────────────────
print('=' * 60)
print('  MercadoKwanza — Transação Distribuída (2PC Simplificado)')
print('=' * 60)

no_luanda   = None
no_benguela = None

try:
    # Estabelecer ligações
    no_luanda   = conectar(3306)
    no_benguela = conectar(3307)
    cur_l = no_luanda.cursor()
    cur_b = no_benguela.cursor()
    log('Sistema', 'Ligações estabelecidas', 'OK')

    # ────────────────────────────────────────────────────────────────
    # FASE 1 — Verificar e decrementar stock em Benguela
    # ────────────────────────────────────────────────────────────────
    cur_b.execute(
        'SELECT quantidade FROM STOCK WHERE produto_id = %s AND loja_id = %s FOR UPDATE',
        (PRODUTO_ID, LOJA_BENGUELA)
    )
    resultado = cur_b.fetchone()

    if resultado is None:
        raise Exception(f'Produto {PRODUTO_ID} não encontrado na loja {LOJA_BENGUELA}')

    stock_actual = resultado[0]
    log('Benguela', f'Stock actual produto {PRODUTO_ID}', f'{stock_actual} unidades')

    if stock_actual < QUANTIDADE:
        raise Exception(
            f'Stock insuficiente: disponível={stock_actual}, pedido={QUANTIDADE}'
        )

    cur_b.execute(
        'UPDATE STOCK SET quantidade = quantidade - %s '
        'WHERE produto_id = %s AND loja_id = %s',
        (QUANTIDADE, PRODUTO_ID, LOJA_BENGUELA)
    )
    log('Benguela', f'UPDATE STOCK -={QUANTIDADE}', 'OK')

    # ────────────────────────────────────────────────────────────────
    # FASE 2 — Registar a venda em Luanda
    # ────────────────────────────────────────────────────────────────

    # DESCOMENTE a linha abaixo para simular uma falha artificial antes do INSERT:
    # raise Exception('Falha simulada artificialmente antes do INSERT em Luanda')

    total_venda = QUANTIDADE * PRECO_UNIT

    cur_l.execute(
        'INSERT INTO VENDA (loja_id, cliente_id, data_venda, total) '
        'VALUES (%s, %s, NOW(), %s)',
        (LOJA_LUANDA, CLIENTE_ID, total_venda)
    )
    venda_id = cur_l.lastrowid
    log('Luanda', f'INSERT VENDA id={venda_id}', 'OK')

    cur_l.execute(
        'INSERT INTO ITEM_VENDA (venda_id, produto_id, qtd, preco_unit, desconto) '
        'VALUES (%s, %s, %s, %s, %s)',
        (venda_id, PRODUTO_ID, QUANTIDADE, PRECO_UNIT, 0.0)
    )
    log('Luanda', f'INSERT ITEM_VENDA venda_id={venda_id}', 'OK')

    # ────────────────────────────────────────────────────────────────
    # FASE 3 — Two-Phase Commit (COMMIT nos dois nós)
    # ────────────────────────────────────────────────────────────────
    no_benguela.commit()
    log('Benguela', 'COMMIT', 'executado')

    no_luanda.commit()
    log('Luanda', 'COMMIT', 'executado')

    print('\n✓ Transação concluída com sucesso em ambos os nós.')
    print(f'  Venda registada: id={venda_id} | Total: {total_venda:,.2f} Kz')

except Exception as e:
    # ────────────────────────────────────────────────────────────────
    # ROLLBACK em caso de qualquer erro
    # ────────────────────────────────────────────────────────────────
    log('Sistema', 'ERRO detectado', str(e))
    if no_benguela:
        no_benguela.rollback()
        log('Benguela', 'ROLLBACK', 'executado')
    if no_luanda:
        no_luanda.rollback()
        log('Luanda', 'ROLLBACK', 'executado')
    print(f'\n✗ Transação cancelada. Motivo: {e}')

finally:
    # Fechar cursores e ligações
    if no_luanda:
        no_luanda.close()
    if no_benguela:
        no_benguela.close()
    print('  Ligações encerradas.\n')

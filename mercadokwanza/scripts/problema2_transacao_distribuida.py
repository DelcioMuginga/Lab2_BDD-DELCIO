#!/usr/bin/env python3
# =====================================================================
#  MercadoKwanza — PARTE 2 | PROBLEMA 2 — CENÁRIO A (Grupo 7)
#  Transação Distribuída: venda interfilial com falha no COMMIT de Luanda
#
#  Cenário: cliente de Luanda (cliente_id=42) compra produto cujo stock
#  existe APENAS numa loja de Benguela (loja_id=6).
#  - Nó Benguela: decrementa stock
#  - Nó Luanda:   regista a venda + itens
#  - Simulação de falha entre o COMMIT de Benguela e o de Luanda
#  - Verificação de ROLLBACK total
#
#  Modo de uso:
#    python scripts/problema2_transacao_distribuida.py          # sucesso
#    python scripts/problema2_transacao_distribuida.py --falha  # simula falha
#
#  Pré-requisito: pip install mysql-connector-python
# =====================================================================

import mysql.connector
import datetime
import sys

# ── Modo de execução ─────────────────────────────────────────────────
SIMULAR_FALHA = '--falha' in sys.argv

# ── Parâmetros da transação ──────────────────────────────────────────
PRODUTO_ID    = 5     # Produto a vender (deve existir com stock > 0 em Benguela)
LOJA_BENGUELA = 6     # Loja de origem do stock (provincia_id = 2)
LOJA_LUANDA   = 1     # Loja onde a venda é registada (provincia_id = 1)
CLIENTE_ID    = 42    # Cliente de Luanda
QUANTIDADE    = 10    # Unidades a vender
PRECO_UNIT    = 1500  # Preço unitário em Kz


# ── Função de log com timestamp preciso ──────────────────────────────
def log(no: str, operacao: str, resultado: str) -> None:
    ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]
    estado = '✓' if resultado in ('OK', 'executado') else ('✗' if 'ERRO' in resultado or 'ROLLBACK' in resultado else '→')
    print(f'[{ts}] {estado} [{no:12}] {operacao:42} -> {resultado}')


# ── Função de conexão ────────────────────────────────────────────────
def conectar(porta: int):
    return mysql.connector.connect(
        host='127.0.0.1',
        port=porta,
        user='root',
        password='kwanza2024',
        database='mercadokwanza',
        autocommit=False          # CRÍTICO: controlo manual do COMMIT/ROLLBACK
    )


# ── Função: mostrar estado antes e depois ────────────────────────────
def mostrar_estado(label: str):
    conn_b = mysql.connector.connect(host='127.0.0.1', port=3307,
        user='root', password='kwanza2024', database='mercadokwanza')
    conn_l = mysql.connector.connect(host='127.0.0.1', port=3306,
        user='root', password='kwanza2024', database='mercadokwanza')
    cb = conn_b.cursor(); cl = conn_l.cursor()

    cb.execute('SELECT quantidade FROM STOCK WHERE produto_id=%s AND loja_id=%s',
               (PRODUTO_ID, LOJA_BENGUELA))
    row_b = cb.fetchone()
    cl.execute('SELECT COUNT(*) FROM VENDA')
    row_l = cl.fetchone()

    print(f'\n  ── Estado {label} ──')
    print(f'     Stock produto {PRODUTO_ID} em Benguela (loja {LOJA_BENGUELA}): '
          f'{row_b[0] if row_b else "N/A"} unidades')
    print(f'     Total de vendas em Luanda: {row_l[0]}')
    print()
    for c in [conn_b, conn_l]: c.close()


# ════════════════════════════════════════════════════════════════════
print('=' * 62)
print('  MercadoKwanza — Problema 2, Cenário A')
print('  Transação Distribuída com Two-Phase Commit Simplificado')
if SIMULAR_FALHA:
    print('  *** MODO: SIMULAÇÃO DE FALHA — vai provocar ROLLBACK ***')
print('=' * 62)

mostrar_estado('ANTES da transação')

no_luanda   = None
no_benguela = None

try:
    # ── Estabelecer ligações ─────────────────────────────────────────
    no_luanda   = conectar(3306)
    no_benguela = conectar(3307)
    cur_l = no_luanda.cursor()
    cur_b = no_benguela.cursor()
    log('Sistema', 'Ligações Luanda (3306) + Benguela (3307)', 'OK')

    # ════════════════════════════════════════════════════════════════
    # FASE 1 — VERIFICAR E BLOQUEAR STOCK EM BENGUELA
    # FOR UPDATE: bloqueia o registo para evitar race condition
    # ════════════════════════════════════════════════════════════════
    cur_b.execute(
        'SELECT quantidade FROM STOCK '
        'WHERE produto_id = %s AND loja_id = %s FOR UPDATE',
        (PRODUTO_ID, LOJA_BENGUELA)
    )
    resultado = cur_b.fetchone()
    log('Benguela', f'SELECT ... FOR UPDATE produto={PRODUTO_ID} loja={LOJA_BENGUELA}', 'OK — registo bloqueado')

    if resultado is None:
        raise Exception(f'Produto {PRODUTO_ID} não existe na loja {LOJA_BENGUELA}')

    stock_actual = resultado[0]
    log('Benguela', f'Stock actual do produto {PRODUTO_ID}', f'{stock_actual} unidades disponíveis')

    if stock_actual < QUANTIDADE:
        raise Exception(
            f'Stock insuficiente — disponível: {stock_actual}, pedido: {QUANTIDADE}'
        )

    # ════════════════════════════════════════════════════════════════
    # FASE 2 — DECREMENTAR STOCK EM BENGUELA
    # ════════════════════════════════════════════════════════════════
    cur_b.execute(
        'UPDATE STOCK SET quantidade = quantidade - %s, atualizado_em = NOW() '
        'WHERE produto_id = %s AND loja_id = %s',
        (QUANTIDADE, PRODUTO_ID, LOJA_BENGUELA)
    )
    log('Benguela', f'UPDATE STOCK quantidade -= {QUANTIDADE}',
        f'OK — novo valor: {stock_actual - QUANTIDADE} unidades')

    # ════════════════════════════════════════════════════════════════
    # PONTO DE FALHA SIMULADA
    # Em modo --falha, a excepção é lançada AQUI:
    # depois do UPDATE em Benguela mas ANTES dos INSERTs em Luanda.
    # Isto representa uma falha de rede ou crash da aplicação.
    # ════════════════════════════════════════════════════════════════
    if SIMULAR_FALHA:
        log('Sistema', 'Falha artificial injectada (--falha)', 'ERRO — a simular crash')
        raise Exception('Falha de rede simulada entre Benguela e Luanda')

    # ════════════════════════════════════════════════════════════════
    # FASE 3 — REGISTAR VENDA EM LUANDA
    # ════════════════════════════════════════════════════════════════
    total_venda = QUANTIDADE * PRECO_UNIT

    cur_l.execute(
        'INSERT INTO VENDA (loja_id, cliente_id, data_venda, total) '
        'VALUES (%s, %s, NOW(), %s)',
        (LOJA_LUANDA, CLIENTE_ID, total_venda)
    )
    venda_id = cur_l.lastrowid
    log('Luanda', f'INSERT VENDA (loja={LOJA_LUANDA}, cliente={CLIENTE_ID})',
        f'OK — venda_id={venda_id}, total={total_venda:,.0f} Kz')

    cur_l.execute(
        'INSERT INTO ITEM_VENDA (venda_id, produto_id, qtd, preco_unit, desconto) '
        'VALUES (%s, %s, %s, %s, %s)',
        (venda_id, PRODUTO_ID, QUANTIDADE, PRECO_UNIT, 0.0)
    )
    log('Luanda', f'INSERT ITEM_VENDA (venda_id={venda_id})', 'OK')

    # ════════════════════════════════════════════════════════════════
    # FASE 4 — TWO-PHASE COMMIT
    # COMMIT em Benguela primeiro, depois em Luanda
    # ════════════════════════════════════════════════════════════════
    no_benguela.commit()
    log('Benguela', 'COMMIT', 'executado')

    no_luanda.commit()
    log('Luanda', 'COMMIT', 'executado')

    print(f'\n  ✓ Transação concluída com sucesso em ambos os nós.')
    print(f'    Produto {PRODUTO_ID} | Qty: {QUANTIDADE} | Total: {total_venda:,.0f} Kz')

except Exception as e:
    # ════════════════════════════════════════════════════════════════
    # ROLLBACK — em caso de qualquer erro, desfazer em AMBOS os nós
    # ════════════════════════════════════════════════════════════════
    print(f'\n  ✗ Erro detectado: {e}')
    if no_benguela:
        no_benguela.rollback()
        log('Benguela', 'ROLLBACK', 'executado')
    if no_luanda:
        no_luanda.rollback()
        log('Luanda', 'ROLLBACK', 'executado')

finally:
    if no_luanda:   no_luanda.close()
    if no_benguela: no_benguela.close()
    log('Sistema', 'Ligações encerradas', 'OK')

mostrar_estado('APÓS a transação')

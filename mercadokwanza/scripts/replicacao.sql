-- =====================================================================
--  MercadoKwanza — Configuração da Replicação Master-Slave
--  Base de Dados II | ISPTEC | Lab #02 — Fase 3
--  Executar APÓS o cluster estar activo (docker compose up -d)
-- =====================================================================

-- =====================================================================
-- PASSO 1 — Verificar status do Master (Luanda)
-- Executar no nó Luanda: docker exec -it no-luanda mysql -uroot -pkwanza2024
-- =====================================================================

-- Ver o ficheiro e posição actual do binary log:
SHOW MASTER STATUS\G

-- Anotar os valores:
--   File:     mysql-bin.000001  (pode variar)
--   Position: 157               (pode variar)


-- =====================================================================
-- PASSO 2 — Configurar Slave Benguela
-- Executar no nó Benguela: docker exec -it no-benguela mysql -uroot -pkwanza2024
-- =====================================================================

-- ATENÇÃO: Substituir os valores de MASTER_LOG_FILE e MASTER_LOG_POS
--          pelos valores anotados no PASSO 1.
STOP SLAVE;

CHANGE MASTER TO
    MASTER_HOST='no-luanda',
    MASTER_USER='root',
    MASTER_PASSWORD='kwanza2024',
    MASTER_LOG_FILE='mysql-bin.000001',   -- <-- valor real do SHOW MASTER STATUS
    MASTER_LOG_POS=157,                   -- <-- valor real do SHOW MASTER STATUS
    MASTER_CONNECT_RETRY=10,
    GET_MASTER_PUBLIC_KEY=1;

START SLAVE;

-- Verificar estado do Slave:
SHOW SLAVE STATUS\G
-- Campos críticos a observar:
--   Slave_IO_Running:      Yes
--   Slave_SQL_Running:     Yes
--   Seconds_Behind_Master: 0
--   Last_Error:            (deve estar vazio)


-- =====================================================================
-- PASSO 3 — Configurar Slave Huambo
-- Executar no nó Huambo: docker exec -it no-huambo mysql -uroot -pkwanza2024
-- (mesmos comandos do PASSO 2)
-- =====================================================================

STOP SLAVE;

CHANGE MASTER TO
    MASTER_HOST='no-luanda',
    MASTER_USER='root',
    MASTER_PASSWORD='kwanza2024',
    MASTER_LOG_FILE='mysql-bin.000001',
    MASTER_LOG_POS=157,
    MASTER_CONNECT_RETRY=10,
    GET_MASTER_PUBLIC_KEY=1;

START SLAVE;

SHOW SLAVE STATUS\G


-- =====================================================================
-- PASSO 4 — Teste de propagação (executar no Master — Luanda)
-- =====================================================================
USE mercadokwanza;

INSERT INTO PRODUTO (descricao, categoria, preco, activo) VALUES
    ('Sabão Protex 200g',         'Higiene',      850.00, 1),
    ('Arroz Precioso 5kg',        'Alimentação', 3500.00, 1),
    ('Pilha AA Energizer x4',     'Electrónica', 1200.00, 1);

-- Verificar imediatamente nos Slaves:
-- docker exec -it no-benguela mysql -uroot -pkwanza2024 mercadokwanza \
--   -e "SELECT id, descricao, categoria, preco FROM PRODUTO ORDER BY id DESC LIMIT 5;"
-- docker exec -it no-huambo mysql -uroot -pkwanza2024 mercadokwanza \
--   -e "SELECT id, descricao, categoria, preco FROM PRODUTO ORDER BY id DESC LIMIT 5;"


-- =====================================================================
-- PASSO 5 — Simular falha do Master
-- =====================================================================
-- No terminal (bash):
--   docker pause no-luanda
--
-- Tentar leitura no Slave Benguela (deve funcionar):
--   docker exec -it no-benguela mysql -uroot -pkwanza2024 mercadokwanza \
--     -e "SELECT COUNT(*) FROM PRODUTO;"
--
-- Restaurar Master:
--   docker unpause no-luanda
--
-- Verificar sincronização nos Slaves após restauro:
--   docker exec -it no-benguela mysql -uroot -pkwanza2024 \
--     -e "SHOW SLAVE STATUS\G" | grep Seconds_Behind_Master
-- =====================================================================

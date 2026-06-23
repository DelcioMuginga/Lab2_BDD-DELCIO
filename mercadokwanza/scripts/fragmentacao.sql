-- =====================================================================
--  MercadoKwanza — Fragmentação Horizontal e Vertical
--  Base de Dados II | ISPTEC | Lab #02 — Fase 2
--  Executar no nó Luanda: docker exec -it no-luanda mysql -uroot -pkwanza2024 mercadokwanza
-- =====================================================================

USE mercadokwanza;

-- =====================================================================
-- 2.3 — Fragmentação Horizontal de VENDA por Província
-- =====================================================================

-- Fragmento de vendas de Luanda (provincia_id = 1)
CREATE OR REPLACE VIEW frag_venda_luanda AS
    SELECT v.* FROM VENDA v
    JOIN LOJA l ON v.loja_id = l.id
    WHERE l.provincia_id = 1;

-- Fragmento de vendas de Benguela (provincia_id = 2)
CREATE OR REPLACE VIEW frag_venda_benguela AS
    SELECT v.* FROM VENDA v
    JOIN LOJA l ON v.loja_id = l.id
    WHERE l.provincia_id = 2;

-- Fragmento de vendas de Huambo (provincia_id = 3)
CREATE OR REPLACE VIEW frag_venda_huambo AS
    SELECT v.* FROM VENDA v
    JOIN LOJA l ON v.loja_id = l.id
    WHERE l.provincia_id = 3;

-- Verificar completude (soma deve igualar o total):
SELECT 'Luanda'      AS provincia, COUNT(*) AS total FROM frag_venda_luanda
UNION ALL
SELECT 'Benguela'    AS provincia, COUNT(*) AS total FROM frag_venda_benguela
UNION ALL
SELECT 'Huambo'      AS provincia, COUNT(*) AS total FROM frag_venda_huambo
UNION ALL
SELECT 'TOTAL GERAL' AS provincia, COUNT(*) AS total FROM VENDA;


-- =====================================================================
-- Fragmentação Vertical de PRODUTO
-- Atributos de catálogo (descricao, categoria) vs comerciais (preco, activo)
-- =====================================================================

-- Fragmento vertical 1 — Catálogo (dados descritivos)
CREATE OR REPLACE VIEW frag_produto_catalogo AS
    SELECT id, descricao, categoria
    FROM PRODUTO;

-- Fragmento vertical 2 — Comercial (dados de preço e disponibilidade)
CREATE OR REPLACE VIEW frag_produto_comercial AS
    SELECT id, preco, activo
    FROM PRODUTO;

-- Verificar reconstituição (JOIN pelos dois fragmentos deve reproduzir a tabela original):
SELECT c.id, c.descricao, c.categoria, m.preco, m.activo
FROM frag_produto_catalogo c
JOIN frag_produto_comercial m ON c.id = m.id
LIMIT 10;


-- =====================================================================
-- Fragmentação Horizontal de STOCK por Província (Problema 1)
-- =====================================================================

CREATE OR REPLACE VIEW frag_stock_luanda AS
    SELECT s.* FROM STOCK s
    JOIN LOJA l ON s.loja_id = l.id
    WHERE l.provincia_id = 1;

CREATE OR REPLACE VIEW frag_stock_benguela AS
    SELECT s.* FROM STOCK s
    JOIN LOJA l ON s.loja_id = l.id
    WHERE l.provincia_id = 2;

CREATE OR REPLACE VIEW frag_stock_huambo AS
    SELECT s.* FROM STOCK s
    JOIN LOJA l ON s.loja_id = l.id
    WHERE l.provincia_id = 3;

SELECT 'Luanda'   AS prov, SUM(quantidade) AS stock_total, COUNT(*) AS registos FROM frag_stock_luanda
UNION ALL
SELECT 'Benguela' AS prov, SUM(quantidade) AS stock_total, COUNT(*) AS registos FROM frag_stock_benguela
UNION ALL
SELECT 'Huambo'   AS prov, SUM(quantidade) AS stock_total, COUNT(*) AS registos FROM frag_stock_huambo;


-- =====================================================================
-- Fragmentação Horizontal de CLIENTE por Província (Problema 1 — Cenário B)
-- =====================================================================

CREATE OR REPLACE VIEW frag_cliente_luanda AS
    SELECT * FROM CLIENTE WHERE provincia_id = 1;

CREATE OR REPLACE VIEW frag_cliente_benguela AS
    SELECT * FROM CLIENTE WHERE provincia_id = 2;

CREATE OR REPLACE VIEW frag_cliente_huambo AS
    SELECT * FROM CLIENTE WHERE provincia_id = 3;

-- Verificar completude (propriedade de reconstituição):
SELECT
    (SELECT COUNT(*) FROM frag_cliente_luanda)   +
    (SELECT COUNT(*) FROM frag_cliente_benguela) +
    (SELECT COUNT(*) FROM frag_cliente_huambo)   AS soma_fragmentos,
    (SELECT COUNT(*) FROM CLIENTE)               AS total_geral;

-- Faturamento médio por cliente por província:
SELECT
    p.nome      AS provincia,
    COUNT(DISTINCT c.id)                                AS clientes,
    ROUND(SUM(v.total) / COUNT(DISTINCT c.id), 2)      AS faturamento_medio_por_cliente
FROM CLIENTE c
JOIN PROVINCIA p ON c.provincia_id = p.id
LEFT JOIN VENDA v ON v.cliente_id = c.id
GROUP BY p.nome
ORDER BY faturamento_medio_por_cliente DESC;

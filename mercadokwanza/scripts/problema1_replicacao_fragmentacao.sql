-- =====================================================================
--  MercadoKwanza — PARTE 2 | PROBLEMA 1 — CENÁRIO A (Grupo 7)
--  Replicação de STOCK: inserir 50 produtos e medir propagação temporal
--  Base de Dados II | ISPTEC | Lab #02
--
--  EXECUTAR PASSO A PASSO conforme as instruções de cada bloco.
--  Cluster deve estar activo e replicação configurada antes de começar.
-- =====================================================================

-- =====================================================================
-- PASSO 1 — Estado inicial: contar PRODUTO em todos os nós
-- Correr cada linha no terminal bash ANTES de inserir qualquer coisa
-- =====================================================================
-- docker exec -it no-luanda   mysql -uroot -pkwanza2024 mercadokwanza -e "SELECT COUNT(*) AS total_luanda   FROM PRODUTO;"
-- docker exec -it no-benguela mysql -uroot -pkwanza2024 mercadokwanza -e "SELECT COUNT(*) AS total_benguela FROM PRODUTO;"
-- docker exec -it no-huambo   mysql -uroot -pkwanza2024 mercadokwanza -e "SELECT COUNT(*) AS total_huambo   FROM PRODUTO;"
-- Anotar os 3 valores na tabela de registos do relatório.


-- =====================================================================
-- PASSO 2 — Inserir 50 novos produtos no Master (Luanda)
-- Executar dentro do MySQL do nó Luanda:
--   docker exec -it no-luanda mysql -uroot -pkwanza2024 mercadokwanza
-- =====================================================================
USE mercadokwanza;

INSERT INTO PRODUTO (descricao, categoria, preco, activo) VALUES
  ('Arroz Precioso Extra 2kg',         'Alimentação',  2100.00, 1),
  ('Feijão Vermelho Nacional 1kg',     'Alimentação',   890.00, 1),
  ('Óleo Girassol Fula 1L',            'Alimentação',  1450.00, 1),
  ('Massa Esparguete Catala 500g',     'Alimentação',   680.00, 1),
  ('Leite Condensado Moça 395g',       'Alimentação',   750.00, 1),
  ('Açúcar Refinado Brilhante 1kg',    'Alimentação',   620.00, 1),
  ('Farinha de Trigo Nacional 1kg',    'Alimentação',   540.00, 1),
  ('Atum em Lata Prado 185g',          'Alimentação',   980.00, 1),
  ('Sal Grosso Cabinda 500g',          'Alimentação',   320.00, 1),
  ('Biscoito Cream Cracker 200g',      'Alimentação',   440.00, 1),
  ('Sabão Protex Antibacteriano 90g',  'Higiene',       680.00, 1),
  ('Shampoo Clear Men 200ml',          'Higiene',      1250.00, 1),
  ('Pasta Dentes Colgate Triple 90g',  'Higiene',       840.00, 1),
  ('Desodorante Rexona Men 150ml',     'Higiene',      1380.00, 1),
  ('Papel Higiénico Neve 4un',         'Higiene',       920.00, 1),
  ('Creme Nívea Body Lotion 250ml',    'Higiene',      1650.00, 1),
  ('Fraldas Pampers P 20un',           'Higiene',      3200.00, 1),
  ('Lâmina Gillette Fusion 4un',       'Higiene',      2100.00, 1),
  ('Sabonete Lux Floral 90g',          'Higiene',       480.00, 1),
  ('Champô Johnson Baby 200ml',        'Higiene',      1100.00, 1),
  ('Televisor Hisense 32" HD',         'Electrónica', 45000.00, 1),
  ('Ferro de Engomar Philips 1800W',   'Electrónica',  8500.00, 1),
  ('Ventoinha de Mesa 16" Branca',     'Electrónica',  6200.00, 1),
  ('Carregador Universal Tipo-C 65W',  'Electrónica',  3400.00, 1),
  ('Auricular Bluetooth JBL T110',     'Electrónica',  9800.00, 1),
  ('Extensão Eléctrica 5 Tomadas 2m',  'Electrónica',  2800.00, 1),
  ('Lâmpada LED Osram 9W E27',         'Electrónica',   850.00, 1),
  ('Bateria Portátil Xiaomi 10000mAh', 'Electrónica',  7500.00, 1),
  ('Rato Wireless Logitech M185',      'Electrónica',  4200.00, 1),
  ('Teclado USB Marvo Basic',          'Electrónica',  3100.00, 1),
  ('Calça Jeans Masculina Azul M',     'Vestuário',    6500.00, 1),
  ('Camisa Social Branca Masculina M', 'Vestuário',    5200.00, 1),
  ('Vestido Floral Feminino M',        'Vestuário',    7800.00, 1),
  ('Ténis Adidas Runfalcon 41',        'Vestuário',   18500.00, 1),
  ('Mochila Escolar Preta 20L',        'Vestuário',    8900.00, 1),
  ('Meias Algodão Pack 3 Pares',       'Vestuário',    1450.00, 1),
  ('Toalha de Banho 70x140 Azul',      'Vestuário',    3200.00, 1),
  ('Boné Nike Dri-Fit Preto',          'Vestuário',    4100.00, 1),
  ('Cinto Couro Castanho Tamanho 90',  'Vestuário',    2900.00, 1),
  ('Pijama Feminino Manga Longa M',    'Vestuário',    5600.00, 1),
  ('Martelo de Bola 500g',             'Ferragens',    3800.00, 1),
  ('Chave de Fendas 6 Peças Set',      'Ferragens',    4500.00, 1),
  ('Fita Métrica 5m Retrátil',         'Ferragens',    1200.00, 1),
  ('Nível de Bolha 60cm Profissional', 'Ferragens',    2800.00, 1),
  ('Parafusos Madeira 4x40 c/100un',   'Ferragens',     680.00, 1),
  ('Tinta Acrílica Branca 18L Priu',   'Ferragens',   12500.00, 1),
  ('Rebarbadora Vonder 115mm 710W',    'Ferragens',   22000.00, 1),
  ('Escova de Arame Circular 115mm',   'Ferragens',    1850.00, 1),
  ('Lixa de Parede Grão 80 c/10un',    'Ferragens',     420.00, 1),
  ('Serra Manual 20 Dentes por cm',    'Ferragens',    3600.00, 1);

-- Anotar o timestamp exacto da inserção (usar NOW() abaixo):
SELECT NOW() AS timestamp_insercao, COUNT(*) AS total_atual FROM PRODUTO;


-- =====================================================================
-- PASSO 3 — Verificar propagação IMEDIATAMENTE após inserção
-- Correr no terminal bash logo após o INSERT acima (< 2 segundos)
-- =====================================================================
-- docker exec -it no-benguela mysql -uroot -pkwanza2024 mercadokwanza \
--   -e "SELECT NOW() AS verificado_em, COUNT(*) AS total_benguela FROM PRODUTO;"


-- =====================================================================
-- PASSO 4 — Aguardar 5 segundos e verificar novamente
-- =====================================================================
-- docker exec -it no-benguela mysql -uroot -pkwanza2024 mercadokwanza \
--   -e "SELECT NOW() AS verificado_em, COUNT(*) AS total_benguela FROM PRODUTO;"
-- docker exec -it no-huambo mysql -uroot -pkwanza2024 mercadokwanza \
--   -e "SELECT NOW() AS verificado_em, COUNT(*) AS total_huambo FROM PRODUTO;"


-- =====================================================================
-- PASSO 5 — Medir atraso durante a inserção (executar em Benguela)
-- =====================================================================
-- docker exec -it no-benguela mysql -uroot -pkwanza2024 \
--   -e "SHOW SLAVE STATUS\G" | grep -E "Seconds_Behind|Slave_IO|Slave_SQL|Last_Error"


-- =====================================================================
-- PASSO 6 — Criar views de fragmentação de STOCK por província
-- Executar no nó Luanda (dentro do MySQL)
-- =====================================================================
USE mercadokwanza;

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

-- Distribuição do stock total por fragmento:
SELECT 'Luanda'   AS provincia, SUM(quantidade) AS stock_total, COUNT(*) AS registos_stock
FROM frag_stock_luanda
UNION ALL
SELECT 'Benguela' AS provincia, SUM(quantidade) AS stock_total, COUNT(*) AS registos_stock
FROM frag_stock_benguela
UNION ALL
SELECT 'Huambo'   AS provincia, SUM(quantidade) AS stock_total, COUNT(*) AS registos_stock
FROM frag_stock_huambo
UNION ALL
SELECT 'TOTAL GERAL', SUM(quantidade), COUNT(*)
FROM STOCK;


-- =====================================================================
-- PASSO 7 — Verificar os 50 novos produtos nos Slaves (Benguela)
-- Executar no nó Benguela (dentro do MySQL)
-- =====================================================================
-- USE mercadokwanza;
-- SELECT id, descricao, categoria, preco
-- FROM PRODUTO
-- ORDER BY id DESC
-- LIMIT 10;

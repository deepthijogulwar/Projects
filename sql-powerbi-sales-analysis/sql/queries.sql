-- =====================================================================
-- Business questions answered with SQL  (run against data/store.db)
-- Revenue is computed by JOINing orders to products: quantity * unit_price
-- =====================================================================

-- 1) Headline KPIs: total orders, total revenue, average order value
SELECT
    COUNT(*)                                   AS total_orders,
    SUM(o.quantity * p.unit_price)             AS total_revenue,
    ROUND(AVG(o.quantity * p.unit_price), 0)   AS avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;

-- 2) Revenue by product category  (JOIN + GROUP BY)
SELECT
    p.category,
    SUM(o.quantity * p.unit_price) AS revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC;

-- 3) Top 5 customers by total spend  (two JOINs)
SELECT
    c.customer_name,
    c.city,
    SUM(o.quantity * p.unit_price) AS total_spend
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products  p ON o.product_id  = p.product_id
GROUP BY c.customer_id
ORDER BY total_spend DESC
LIMIT 5;

-- 4) Revenue by customer segment
SELECT
    c.segment,
    SUM(o.quantity * p.unit_price) AS revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products  p ON o.product_id  = p.product_id
GROUP BY c.segment
ORDER BY revenue DESC;

-- 5) Monthly revenue trend
SELECT
    substr(o.order_date, 1, 7) AS month,
    SUM(o.quantity * p.unit_price) AS revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY month
ORDER BY month;

-- 6) Best-selling products by units sold
SELECT
    p.product_name,
    SUM(o.quantity) AS units_sold
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.product_id
ORDER BY units_sold DESC
LIMIT 5;

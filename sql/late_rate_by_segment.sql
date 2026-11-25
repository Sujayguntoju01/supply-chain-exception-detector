-- Late-delivery rate by shipping mode and market, used in the README / reports.
SELECT
    shipping_mode,
    market,
    COUNT(*)                         AS order_items,
    ROUND(AVG(is_late) * 100, 1)     AS late_pct,
    ROUND(AVG(days_real - days_scheduled), 2) AS avg_delay_days
FROM orders
GROUP BY shipping_mode, market
ORDER BY late_pct DESC;

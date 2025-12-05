CREATE OR REPLACE VIEW daily_spending_summary AS
SELECT 
    t.transaction_date,
    s.store_name,
    tc.name as group,
    t.currency,
    COUNT(t.transaction_id) as count,
    SUM(t.total) as amout
FROM transaction t
JOIN store s ON t.store_id = s.store_id
LEFT JOIN transaction_category tc ON t.transaction_category_id = tc.category_id
GROUP BY s.store_name, tc.name, t.transaction_date, t.currency
ORDER BY t.transaction_date DESC, s.store_name, tc.name;
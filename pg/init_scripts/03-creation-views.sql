-- ============================================================================
-- CRÉATION DES VUES
-- ============================================================================

CREATE VIEW v_transactions_summary AS
SELECT 
    t.transaction_id,
    t.transaction_date,
    t.transaction_time,
    t.total,
    t.currency,
    t.payment_method,
    s.store_name,
    s.city,
    s.country_code,
    tc.name as transaction_category,
    COUNT(i.item_id) as item_count,
    t.source
FROM transaction t
JOIN store s ON t.store_id = s.store_id
LEFT JOIN transaction_category tc ON t.transaction_category_id = tc.category_id
LEFT JOIN transaction_item_mapping tim ON t.transaction_id = tim.transaction_id
LEFT JOIN item i ON tim.item_id = i.item_id
GROUP BY t.transaction_id, s.store_id, tc.category_id;

CREATE VIEW v_spending_by_category AS
SELECT 
    t.currency,
    c.category_main,
    c.category_sub,
    DATE_TRUNC('month', t.transaction_date) as month,
    COUNT(i.item_id) as item_count,
    SUM(i.total_price) as total_spent
FROM transaction_item_mapping tim
JOIN item i ON tim.item_id = i.item_id
JOIN item_category c ON i.category_id = c.category_id
JOIN transaction t ON tim.transaction_id = t.transaction_id
GROUP BY t.currency, c.category_main, c.category_sub, month;

-- ============================================================================
-- CRÉATION DES FONCTIONS ET TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_store_updated_at BEFORE UPDATE ON store
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signal_group_updated_at BEFORE UPDATE ON signal_group
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- AFFICHAGE DU RÉSUMÉ
-- ============================================================================

SELECT COUNT(*) as categories_inserted FROM item_category;
SELECT 'Données, vues et fonctions créées avec succès!' as status;
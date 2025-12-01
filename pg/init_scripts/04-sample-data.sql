-- ============================================================================
-- SCRIPT DE DONNÉES FICTIVES POUR LE DASHBOARD
-- ============================================================================
-- Ce script peuple les tables avec des données réalistes pour le développement
-- et la création de dashboards

-- ============================================================================
-- 1. STORES (Magasins)
-- ============================================================================
INSERT INTO store (store_name, address, postal_code, city, country_code, phone) VALUES
('Migros', 'Rue du Marché 15', '1204', 'Genève', 'CH', '+41 22 123 45 67'),
('Coop', 'Avenue de la Gare 42', '1003', 'Lausanne', 'CH', '+41 21 234 56 78'),
('Denner', 'Rue de la Paix 8', '1204', 'Genève', 'CH', '+41 22 345 67 89'),
('Aldi', 'Boulevard des Philosophes 20', '1205', 'Genève', 'CH', '+41 22 456 78 90'),
('Lidl', 'Avenue de France 10', '1202', 'Genève', 'CH', '+41 22 567 89 01'),
('Manor', 'Rue du Rhône 42', '1204', 'Genève', 'CH', '+41 22 678 90 12'),
('IKEA', 'Route de Vernier 1', '1214', 'Vernier', 'CH', '+41 22 789 01 23'),
('Decathlon', 'Route de Chancy 45', '1213', 'Onex', 'CH', '+41 22 890 12 34'),
('Farmacie Principale', 'Rue du Mont-Blanc 18', '1201', 'Genève', 'CH', '+41 22 901 23 45'),
('Shell', 'Route de Lausanne 150', '1292', 'Chambésy', 'CH', '+41 22 012 34 56'),
('McDonald''s', 'Rue du Rhône 50', '1204', 'Genève', 'CH', '+41 22 123 45 67'),
('Starbucks', 'Place du Molard 1', '1204', 'Genève', 'CH', '+41 22 234 56 78'),
('Migros Restaurant', 'Rue de Lausanne 120', '1202', 'Genève', 'CH', '+41 22 345 67 89'),
('Coop Pronto', 'Avenue de Champel 10', '1206', 'Genève', 'CH', '+41 22 456 78 90'),
('BP', 'Route de Chancy 200', '1213', 'Onex', 'CH', '+41 22 567 89 01')
ON CONFLICT (store_name, city, postal_code) DO NOTHING;

-- ============================================================================
-- 2. SIGNAL_SENDER (Expéditeurs)
-- ============================================================================
INSERT INTO signal_sender (signal_uuid, phone_number, contact_name) VALUES
('6aef6f35-7fcd-44c3-a6a4-e4c69f43535c', '+41791234567', 'Carmelo'),
('8bcd9f46-8gde-55d4-b7b5-f5d70g54646d', '+41792345678', 'Heather'),
('9cde0g57-9hef-66e5-c8c6-g6e81h65757e', '+41793456789', 'Neon'),
('0def1h68-0ifg-77f6-d9d7-h7f92i76868f', '+41794567890', 'Alice'),
('1efg2i79-1jgh-88g7-e0e8-i8g03j87979g', '+41795678901', 'Bob')
ON CONFLICT (signal_uuid) DO NOTHING;

-- ============================================================================
-- 3. SIGNAL_GROUP (Groupes Signal)
-- ============================================================================
INSERT INTO signal_group (signal_group_id, group_name) VALUES
('group.1234567890abcdef', 'Tickets 🧾'),
('group.abcdef1234567890', 'Famille'),
('group.9876543210fedcba', 'Amis')
ON CONFLICT (signal_group_id) DO NOTHING;

-- ============================================================================
-- 4. SIGNAL_MESSAGE (Messages Signal)
-- ============================================================================
-- Générer des messages sur les 3 derniers mois
INSERT INTO signal_message (sender_id, group_id, timestamp, text_content, is_group_message, signal_account, processed)
SELECT 
    s.sender_id,
    g.group_id,
    CURRENT_TIMESTAMP - (random() * INTERVAL '90 days') - (random() * INTERVAL '1 day'),
    CASE 
        WHEN random() > 0.5 THEN 'Voici le ticket'
        ELSE NULL
    END,
    TRUE,
    '+41791234567',
    TRUE
FROM signal_sender s
CROSS JOIN signal_group g
WHERE g.group_name = 'Tickets 🧾'
LIMIT 50;

-- ============================================================================
-- 5. ATTACHMENT (Pièces jointes)
-- ============================================================================
INSERT INTO attachment (signal_attachment_id, content_type, filename, file_size, upload_timestamp_ms, file_path)
SELECT 
    'att_' || generate_series(1, 50),
    'image/jpeg',
    'receipt_' || generate_series(1, 50) || '.jpg',
    (random() * 2000000 + 500000)::INTEGER, -- Taille entre 500KB et 2.5MB
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - random() * INTERVAL '90 days')) * 1000::BIGINT,
    '/data/attachments/receipt_' || generate_series(1, 50) || '.jpg';

-- ============================================================================
-- 6. MESSAGE_ATTACHMENT_MAPPING
-- ============================================================================
INSERT INTO message_attachment_mapping (message_id, attachment_id)
SELECT 
    m.message_id,
    a.attachment_id
FROM signal_message m
CROSS JOIN LATERAL (
    SELECT attachment_id 
    FROM attachment 
    ORDER BY random() 
    LIMIT 1
) a
WHERE m.processed = TRUE
LIMIT 50
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 7. TRANSACTION (Transactions)
-- ============================================================================
-- Générer des transactions variées sur les 3 derniers mois
WITH store_data AS (
    SELECT store_id, store_name FROM store ORDER BY random()
),
sender_data AS (
    SELECT sender_id, contact_name FROM signal_sender
),
category_data AS (
    SELECT category_id, name FROM transaction_category
),
message_data AS (
    SELECT message_id, sender_id, timestamp FROM signal_message WHERE processed = TRUE
)
INSERT INTO transaction (
    message_id, store_id, transaction_category_id, receipt_number,
    transaction_date, transaction_time, currency, total, payment_method, source
)
SELECT 
    m.message_id,
    s.store_id,
    c.category_id,
    'RCP-' || LPAD((ROW_NUMBER() OVER ())::TEXT, 6, '0'),
    DATE(m.timestamp),
    TIME(m.timestamp),
    'CHF',
    (random() * 200 + 10)::DECIMAL(10, 2), -- Montant entre 10 et 210 CHF
    CASE 
        WHEN random() > 0.6 THEN 'Carte bancaire'
        WHEN random() > 0.3 THEN 'Espèces'
        ELSE 'Twint'
    END,
    'Signal'
FROM message_data m
CROSS JOIN LATERAL (SELECT store_id FROM store_data LIMIT 1) s
CROSS JOIN LATERAL (SELECT category_id FROM category_data ORDER BY random() LIMIT 1) c
LIMIT 50;

-- ============================================================================
-- 8. TRANSACTION_ATTACHMENT_MAPPING
-- ============================================================================
INSERT INTO transaction_attachment_mapping (transaction_id, attachment_id)
SELECT 
    t.transaction_id,
    mam.attachment_id
FROM transaction t
JOIN signal_message m ON t.message_id = m.message_id
JOIN message_attachment_mapping mam ON m.message_id = mam.message_id
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 9. ITEM (Articles)
-- ============================================================================
-- Générer des articles variés pour chaque transaction
DO $$
DECLARE
    trans_record RECORD;
    item_count INTEGER;
    cat_record RECORD;
    line_num INTEGER;
BEGIN
    FOR trans_record IN SELECT transaction_id FROM transaction LOOP
        item_count := (random() * 5 + 2)::INTEGER; -- Entre 2 et 7 articles
        line_num := 1;
        
        FOR cat_record IN 
            SELECT category_id 
            FROM item_category 
            WHERE active = TRUE
            ORDER BY random() 
            LIMIT item_count
        LOOP
            INSERT INTO item (
                product_name, product_reference, brand, quantity, unit_price, total_price, vat_rate, category_id, line_number
            ) VALUES (
                CASE 
                    WHEN random() > 0.8 THEN 'Pommes Gala'
                    WHEN random() > 0.6 THEN 'Lait entier 1L'
                    WHEN random() > 0.4 THEN 'Pain de campagne'
                    WHEN random() > 0.2 THEN 'Pâtes spaghetti 500g'
                    ELSE 'Tomates cerises 250g'
                END,
                'REF-' || LPAD((line_num + trans_record.transaction_id * 100)::TEXT, 8, '0'),
                CASE 
                    WHEN random() > 0.7 THEN 'Migros'
                    WHEN random() > 0.4 THEN 'Coop'
                    WHEN random() > 0.2 THEN 'Marque propre'
                    ELSE 'Autre'
                END,
                (random() * 3 + 1)::DECIMAL(10, 3),
                (random() * 10 + 2)::DECIMAL(10, 2),
                (random() * 30 + 5)::DECIMAL(10, 2),
                CASE 
                    WHEN random() > 0.5 THEN '7.7%'
                    ELSE '2.5%'
                END,
                cat_record.category_id,
                line_num
            );
            line_num := line_num + 1;
        END LOOP;
    END LOOP;
END $$;

-- ============================================================================
-- 10. TRANSACTION_ITEM_MAPPING
-- ============================================================================
-- Lier les articles aux transactions de manière cohérente
-- On lie chaque article à une transaction de manière séquentielle
DO $$
DECLARE
    trans_record RECORD;
    item_record RECORD;
    item_counter INTEGER := 0;
    current_trans_id INTEGER;
BEGIN
    current_trans_id := NULL;
    
    FOR item_record IN SELECT item_id FROM item ORDER BY item_id LOOP
        -- Changer de transaction tous les 3-7 articles
        IF current_trans_id IS NULL OR item_counter >= (random() * 4 + 3)::INTEGER THEN
            SELECT transaction_id INTO current_trans_id 
            FROM transaction 
            WHERE transaction_id NOT IN (
                SELECT transaction_id FROM transaction_item_mapping
            )
            ORDER BY random() 
            LIMIT 1;
            
            IF current_trans_id IS NULL THEN
                -- Si toutes les transactions ont des articles, prendre une au hasard
                SELECT transaction_id INTO current_trans_id 
                FROM transaction 
                ORDER BY random() 
                LIMIT 1;
            END IF;
            
            item_counter := 0;
        END IF;
        
        INSERT INTO transaction_item_mapping (transaction_id, item_id)
        VALUES (current_trans_id, item_record.item_id)
        ON CONFLICT DO NOTHING;
        
        item_counter := item_counter + 1;
    END LOOP;
END $$;

-- Ajuster les totaux des transactions pour qu'ils correspondent à la somme des articles
UPDATE transaction t
SET total = (
    SELECT COALESCE(SUM(i.total_price), t.total)
    FROM transaction_item_mapping tim
    JOIN item i ON tim.item_id = i.item_id
    WHERE tim.transaction_id = t.transaction_id
)
WHERE EXISTS (
    SELECT 1 
    FROM transaction_item_mapping tim 
    WHERE tim.transaction_id = t.transaction_id
);

-- ============================================================================
-- STATISTIQUES
-- ============================================================================
SELECT 
    'Données fictives insérées:' as info,
    (SELECT COUNT(*) FROM store) as stores,
    (SELECT COUNT(*) FROM signal_sender) as senders,
    (SELECT COUNT(*) FROM signal_group) as groups,
    (SELECT COUNT(*) FROM signal_message) as messages,
    (SELECT COUNT(*) FROM attachment) as attachments,
    (SELECT COUNT(*) FROM transaction) as transactions,
    (SELECT COUNT(*) FROM item) as items,
    (SELECT SUM(total) FROM transaction) as total_amount_chf;


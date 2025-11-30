-- ============================================================================
-- SCRIPT DE CRÉATION DE LA BASE DE DONNÉES - RECEIPT PROCESSING SYSTEM
-- ============================================================================
-- Base de données pour le traitement des tickets de caisse via Signal
-- Auteur: Carmelo
-- Date: 2025-11-29
-- ============================================================================

-- Création de la base de données (optionnel - à exécuter séparément si nécessaire)
-- CREATE DATABASE receipt_processing;
-- \c receipt_processing;

-- ============================================================================
-- SUPPRESSION DES TABLES EXISTANTES (optionnel - pour réinitialiser)
-- ============================================================================
-- Décommenter ces lignes si vous voulez recréer les tables
/*
DROP TABLE IF EXISTS transaction_attachments CASCADE;
DROP TABLE IF EXISTS items CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS attachments CASCADE;
DROP TABLE IF EXISTS signal_messages CASCADE;
DROP TABLE IF EXISTS signal_groups CASCADE;
DROP TABLE IF EXISTS signal_senders CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS stores CASCADE;
*/

-- ============================================================================
-- TABLE 1: STORES (Magasins)
-- ============================================================================
CREATE TABLE stores (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    postal_code VARCHAR(20),
    city VARCHAR(100),
    country_code CHAR(2),  -- CH, IT, FR, DE, etc.
    phone VARCHAR(50),
    
    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les stores
CREATE INDEX idx_stores_name ON stores(store_name);
CREATE INDEX idx_stores_city ON stores(city);
CREATE INDEX idx_stores_country ON stores(country_code);
CREATE INDEX idx_stores_location ON stores(store_name, city, postal_code);

-- Commentaires
COMMENT ON TABLE stores IS 'Table des magasins où les achats sont effectués';
COMMENT ON COLUMN stores.country_code IS 'Code pays ISO 3166-1 alpha-2 (CH, IT, FR, etc.)';

-- ============================================================================
-- TABLE 2: SIGNAL_SENDERS (Émetteurs des messages Signal)
-- ============================================================================
CREATE TABLE signal_senders (
    sender_id SERIAL PRIMARY KEY,
    signal_uuid UUID UNIQUE NOT NULL,  -- UUID de Signal
    phone_number VARCHAR(50),
    contact_name VARCHAR(255),
    
    -- Métadonnées
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0
);

-- Index pour les senders
CREATE INDEX idx_senders_uuid ON signal_senders(signal_uuid);
CREATE INDEX idx_senders_name ON signal_senders(contact_name);

-- Commentaires
COMMENT ON TABLE signal_senders IS 'Personnes qui envoient des tickets via Signal';
COMMENT ON COLUMN signal_senders.signal_uuid IS 'UUID unique de l''utilisateur Signal';

-- ============================================================================
-- TABLE 3: SIGNAL_GROUPS (Groupes Signal)
-- ============================================================================
CREATE TABLE signal_groups (
    group_id SERIAL PRIMARY KEY,
    signal_group_id VARCHAR(255) UNIQUE NOT NULL,  -- ID du groupe Signal
    group_name VARCHAR(255),
    
    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les groups
CREATE INDEX idx_groups_signal_id ON signal_groups(signal_group_id);

-- Commentaires
COMMENT ON TABLE signal_groups IS 'Groupes Signal où les tickets sont partagés';

-- ============================================================================
-- TABLE 4: SIGNAL_MESSAGES (Messages Signal reçus)
-- ============================================================================
CREATE TABLE signal_messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INTEGER,
    group_id INTEGER,
    
    -- Informations du message
    timestamp TIMESTAMP NOT NULL,
    text_content TEXT,
    is_group_message BOOLEAN DEFAULT FALSE,
    signal_account VARCHAR(255),  -- Compte Signal qui a reçu le message
    
    -- Métadonnées
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    
    -- Clés étrangères
    FOREIGN KEY (sender_id) REFERENCES signal_senders(sender_id) ON DELETE SET NULL,
    FOREIGN KEY (group_id) REFERENCES signal_groups(group_id) ON DELETE SET NULL
);

-- Index pour les messages
CREATE INDEX idx_messages_sender ON signal_messages(sender_id);
CREATE INDEX idx_messages_group ON signal_messages(group_id);
CREATE INDEX idx_messages_timestamp ON signal_messages(timestamp);
CREATE INDEX idx_messages_processed ON signal_messages(processed);

-- Commentaires
COMMENT ON TABLE signal_messages IS 'Messages Signal reçus contenant des tickets';
COMMENT ON COLUMN signal_messages.processed IS 'Indique si le message a été traité par Claude';

-- ============================================================================
-- TABLE 5: ATTACHMENTS (Pièces jointes des messages)
-- ============================================================================
CREATE TABLE attachments (
    attachment_id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL,
    
    -- Informations de l'attachment Signal
    signal_attachment_id VARCHAR(255),  -- "2ltlwohfVpAMoERvUG0j.jpg"
    content_type VARCHAR(100),  -- "image/jpeg"
    filename VARCHAR(255),  -- "signal-2025-11-25-231507.jpg"
    file_size INTEGER,  -- en bytes
    upload_timestamp_ms BIGINT,  -- timestamp de l'upload Signal
    
    -- Stockage
    file_path TEXT NOT NULL,  -- Chemin vers le fichier
    
    -- Métadonnées
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Clé étrangère
    FOREIGN KEY (message_id) REFERENCES signal_messages(message_id) ON DELETE CASCADE
);

-- Index pour les attachments
CREATE INDEX idx_attachments_message ON attachments(message_id);
CREATE INDEX idx_attachments_content_type ON attachments(content_type);
CREATE INDEX idx_attachments_signal_id ON attachments(signal_attachment_id);

-- Commentaires
COMMENT ON TABLE attachments IS 'Images et fichiers joints aux messages Signal';
COMMENT ON COLUMN attachments.file_path IS 'Chemin complet vers le fichier sur le système';

-- ============================================================================
-- TABLE 6: TRANSACTIONS (Tickets de caisse)
-- ============================================================================
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,
    message_id INTEGER,  -- Lien vers le message Signal d'origine (optionnel)
    
    -- Informations du ticket
    receipt_number VARCHAR(100),  -- Numéro de ticket du magasin
    transaction_date DATE NOT NULL,
    transaction_time TIME,
    
    -- Montants
    currency CHAR(3) NOT NULL,  -- CHF, EUR, USD
    total DECIMAL(10, 2) NOT NULL,
    
    -- Paiement
    payment_method VARCHAR(50),  -- carte, espèces, autre
    
    -- Métadonnées système
    source VARCHAR(50),  -- signal, email, manual
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    
    -- Clés étrangères
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE RESTRICT,
    FOREIGN KEY (message_id) REFERENCES signal_messages(message_id) ON DELETE SET NULL
);

-- Index pour les transactions
CREATE INDEX idx_transactions_store ON transactions(store_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_currency ON transactions(currency);
CREATE INDEX idx_transactions_message ON transactions(message_id);
CREATE INDEX idx_transactions_date_store ON transactions(transaction_date, store_id);
CREATE INDEX idx_transactions_source ON transactions(source);

-- Commentaires
COMMENT ON TABLE transactions IS 'Tickets de caisse analysés';
COMMENT ON COLUMN transactions.currency IS 'Devise du ticket (CHF, EUR, USD, etc.)';
COMMENT ON COLUMN transactions.source IS 'Source du ticket: signal, email, manual';

-- ============================================================================
-- TABLE 7: TRANSACTION_ATTACHMENTS (Lien N:M entre transactions et images)
-- ============================================================================
CREATE TABLE transaction_attachments (
    transaction_id INTEGER NOT NULL,
    attachment_id INTEGER NOT NULL,
    
    PRIMARY KEY (transaction_id, attachment_id),
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    FOREIGN KEY (attachment_id) REFERENCES attachments(attachment_id) ON DELETE CASCADE
);

-- Index pour la table de liaison
CREATE INDEX idx_trans_att_transaction ON transaction_attachments(transaction_id);
CREATE INDEX idx_trans_att_attachment ON transaction_attachments(attachment_id);

-- Commentaires
COMMENT ON TABLE transaction_attachments IS 'Liaison entre tickets et leurs images (un ticket peut avoir plusieurs images)';

-- ============================================================================
-- TABLE 8: ITEMS (Articles des tickets)
-- ============================================================================
CREATE TABLE items (
    item_id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL,
    
    -- Informations produit
    product_name VARCHAR(500) NOT NULL,
    product_reference VARCHAR(100),
    brand VARCHAR(100),
    
    -- Prix et quantité
    quantity DECIMAL(10, 3) NOT NULL,  -- 3 décimales pour les produits au poids
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    vat_rate VARCHAR(10),  -- "8.1%", "2.6%"
    
    -- Catégorisation
    category_main VARCHAR(100) NOT NULL,
    category_sub VARCHAR(100) NOT NULL,
    
    -- Ordre dans le ticket
    line_number INTEGER,
    
    -- Clé étrangère
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE
);

-- Index pour les items
CREATE INDEX idx_items_transaction ON items(transaction_id);
CREATE INDEX idx_items_category_main ON items(category_main);
CREATE INDEX idx_items_category_sub ON items(category_sub);
CREATE INDEX idx_items_brand ON items(brand);
CREATE INDEX idx_items_categories ON items(category_main, category_sub);
CREATE INDEX idx_items_product_name ON items(product_name);

-- Commentaires
COMMENT ON TABLE items IS 'Articles individuels extraits des tickets';
COMMENT ON COLUMN items.quantity IS 'Quantité (3 décimales pour produits au poids)';
COMMENT ON COLUMN items.line_number IS 'Position de l''article dans le ticket';

-- ============================================================================
-- TABLE 9: CATEGORIES (Référentiel des catégories)
-- ============================================================================
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_main VARCHAR(100) NOT NULL,
    category_sub VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(category_main, category_sub)
);

-- Index pour les catégories
CREATE INDEX idx_categories_main ON categories(category_main);
CREATE INDEX idx_categories_active ON categories(active);

-- Commentaires
COMMENT ON TABLE categories IS 'Référentiel des catégories de dépenses (standard bancaire)';
COMMENT ON COLUMN categories.active IS 'Indique si la catégorie est encore utilisée';

-- ============================================================================
-- INSERTION DES CATÉGORIES DE RÉFÉRENCE
-- ============================================================================

INSERT INTO categories (category_main, category_sub, description) VALUES
-- ALIMENTATION & BOISSONS
('Alimentation et supermarchés', 'Fruits et légumes frais', 'Fruits et légumes frais'),
('Alimentation et supermarchés', 'Viande et charcuterie', 'Viande, volaille et charcuterie'),
('Alimentation et supermarchés', 'Poisson et fruits de mer', 'Poisson et fruits de mer'),
('Alimentation et supermarchés', 'Produits laitiers et œufs', 'Lait, fromage, yaourt, œufs'),
('Alimentation et supermarchés', 'Pain et viennoiseries', 'Pain, croissants, viennoiseries'),
('Alimentation et supermarchés', 'Pâtes, riz et céréales', 'Pâtes, riz, céréales'),
('Alimentation et supermarchés', 'Conserves et produits secs', 'Conserves, légumineuses sèches'),
('Alimentation et supermarchés', 'Produits surgelés', 'Produits surgelés'),
('Alimentation et supermarchés', 'Snacks et confiserie', 'Chips, chocolat, bonbons'),
('Alimentation et supermarchés', 'Condiments et sauces', 'Huile, vinaigre, épices, sauces'),

('Boissons', 'Eau et boissons gazeuses nature', 'Eau plate, gazeuse, eau minérale'),
('Boissons', 'Boissons sucrées (sodas, jus industriels, energy drinks)', 'Coca-Cola, jus industriels, energy drinks'),
('Boissons', 'Alcools et vins', 'Vins, spiritueux'),
('Boissons', 'Bières et cidres', 'Bières et cidres'),
('Boissons', 'Café et thé', 'Café, thé, tisanes'),
('Boissons', 'Jus de fruits 100%', 'Jus de fruits pur jus'),

('Restaurants et cafés', 'Restaurants et cafés', 'Repas au restaurant, café'),
('Bars et vie nocturne', 'Bars et vie nocturne', 'Bars, clubs'),
('Boulangeries et pâtisseries', 'Boulangeries et pâtisseries', 'Boulangeries, pâtisseries'),

-- COMMERCES
('Vêtements et chaussures', 'Vêtements homme', 'Vêtements homme'),
('Vêtements et chaussures', 'Vêtements femme', 'Vêtements femme'),
('Vêtements et chaussures', 'Vêtements enfant', 'Vêtements enfant'),
('Vêtements et chaussures', 'Chaussures ville', 'Chaussures ville'),
('Vêtements et chaussures', 'Sous-vêtements et lingerie', 'Sous-vêtements, lingerie'),
('Vêtements et chaussures', 'Accessoires vestimentaires (ceintures, écharpes, etc.)', 'Ceintures, écharpes, chapeaux'),

('Sport et loisirs', 'Vêtements de sport', 'Vêtements de sport'),
('Sport et loisirs', 'Chaussures de sport', 'Chaussures de sport, baskets'),
('Sport et loisirs', 'Équipement sportif (ballons, raquettes, etc.)', 'Ballons, raquettes, équipement'),
('Sport et loisirs', 'Accessoires fitness (tapis, haltères, etc.)', 'Tapis de yoga, haltères, fitness'),
('Sport et loisirs', 'Activités outdoor (camping, randonnée, ski)', 'Camping, randonnée, ski'),

('Électronique et informatique', 'Informatique et tablettes', 'Ordinateurs, tablettes'),
('Électronique et informatique', 'Téléphonie mobile', 'Téléphones, smartphones'),
('Électronique et informatique', 'Audio et vidéo', 'Casques, enceintes, TV'),
('Électronique et informatique', 'Gaming et consoles', 'Consoles, jeux vidéo'),
('Électronique et informatique', 'Accessoires électroniques (câbles, souris, claviers)', 'Câbles, souris, claviers'),
('Électronique et informatique', 'Consommables électroniques (piles, cartouches)', 'Piles, batteries, cartouches'),

('Meubles et décoration', 'Meubles et décoration', 'Meubles, décoration'),

('Bricolage et jardinage', 'Outils et quincaillerie', 'Outils, vis, clous'),
('Bricolage et jardinage', 'Matériaux de construction', 'Bois, ciment, matériaux'),
('Bricolage et jardinage', 'Peinture et décoration', 'Peinture, papier peint'),
('Bricolage et jardinage', 'Jardinage et plantes', 'Plantes, terreau, outils jardinage'),

('Pharmacie et parapharmacie', 'Médicaments', 'Médicaments'),
('Pharmacie et parapharmacie', 'Compléments alimentaires', 'Vitamines, compléments'),
('Pharmacie et parapharmacie', 'Matériel médical', 'Matériel médical'),

('Librairie et papeterie', 'Librairie et papeterie', 'Livres, papeterie'),

('Jouets et jeux', 'Jouets enfant', 'Jouets pour enfants'),
('Jouets et jeux', 'Jeux de société', 'Jeux de société'),
('Jouets et jeux', 'Loisirs créatifs', 'Loisirs créatifs'),

('Bijouterie et horlogerie', 'Bijouterie et horlogerie', 'Bijoux, montres'),

-- MAISON
('Hygiène et beauté', 'Soins du corps', 'Gel douche, savon, déodorant'),
('Hygiène et beauté', 'Soins du visage', 'Crèmes, nettoyants visage'),
('Hygiène et beauté', 'Cheveux et coiffure', 'Shampoing, après-shampoing'),
('Hygiène et beauté', 'Maquillage', 'Maquillage'),
('Hygiène et beauté', 'Parfumerie', 'Parfums, eaux de toilette'),
('Hygiène et beauté', 'Hygiène bébé', 'Couches, lingettes bébé'),

('Entretien et nettoyage', 'Produits d''entretien', 'Nettoyants, désinfectants'),
('Entretien et nettoyage', 'Lessive et adoucissant', 'Lessive, adoucissant'),
('Entretien et nettoyage', 'Papier et consommables (essuie-tout, mouchoirs)', 'Essuie-tout, mouchoirs, papier toilette'),

('Électroménager', 'Électroménager', 'Électroménager'),
('Quincaillerie et outillage', 'Quincaillerie et outillage', 'Quincaillerie, outils'),

-- SERVICES
('Essence et carburant', 'Essence et carburant', 'Carburant, essence, diesel'),
('Télécommunications', 'Télécommunications', 'Téléphone, internet'),
('Santé et soins médicaux', 'Santé et soins médicaux', 'Consultations, soins'),
('Services professionnels', 'Services professionnels', 'Services professionnels'),

-- LOISIRS & CULTURE
('Divertissement et culture', 'Livres et magazines', 'Livres, magazines'),
('Divertissement et culture', 'Musique et films', 'Musique, films, streaming'),
('Divertissement et culture', 'Billetterie spectacles', 'Cinéma, théâtre, concerts'),

('Voyages et tourisme', 'Voyages et tourisme', 'Voyages, hôtels, transport'),
('Cadeaux et fleurs', 'Cadeaux et fleurs', 'Cadeaux, fleurs'),

-- ANIMAUX
('Animalerie', 'Nourriture pour animaux', 'Croquettes, nourriture animaux'),
('Animalerie', 'Accessoires pour animaux', 'Jouets, accessoires animaux'),
('Animalerie', 'Soins vétérinaires', 'Vétérinaire, soins'),

-- AUTRE
('Divers', 'Divers', 'Autres dépenses non catégorisées'),
('Non catégorisé', 'Non catégorisé', 'Articles non catégorisables');

-- ============================================================================
-- VUES UTILES
-- ============================================================================

-- Vue pour obtenir un résumé des transactions avec infos magasin
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
    COUNT(i.item_id) as item_count,
    t.source
FROM transactions t
JOIN stores s ON t.store_id = s.store_id
LEFT JOIN items i ON t.transaction_id = i.transaction_id
GROUP BY t.transaction_id, s.store_id;

COMMENT ON VIEW v_transactions_summary IS 'Vue récapitulative des transactions avec informations magasin';

-- Vue pour les dépenses par catégorie
CREATE VIEW v_spending_by_category AS
SELECT 
    t.currency,
    i.category_main,
    i.category_sub,
    DATE_TRUNC('month', t.transaction_date) as month,
    COUNT(i.item_id) as item_count,
    SUM(i.total_price) as total_spent
FROM items i
JOIN transactions t ON i.transaction_id = t.transaction_id
GROUP BY t.currency, i.category_main, i.category_sub, month;

COMMENT ON VIEW v_spending_by_category IS 'Dépenses agrégées par catégorie et par mois';

-- ============================================================================
-- FONCTIONS UTILES
-- ============================================================================

-- Fonction pour mettre à jour le timestamp updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour mettre à jour updated_at
CREATE TRIGGER update_stores_updated_at BEFORE UPDATE ON stores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signal_groups_updated_at BEFORE UPDATE ON signal_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- AFFICHAGE DU RÉSUMÉ
-- ============================================================================

SELECT 'Base de données créée avec succès!' as status;

SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- ============================================================================
-- FIN DU SCRIPT
-- ============================================================================
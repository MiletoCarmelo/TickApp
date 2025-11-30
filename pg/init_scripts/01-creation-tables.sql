-- ============================================================================
-- SCRIPT DE CRÉATION DES TABLES - RECEIPT PROCESSING SYSTEM
-- ============================================================================

-- Suppression des tables existantes si nécessaire
DROP TABLE IF EXISTS transaction_item_mapping CASCADE;
DROP TABLE IF EXISTS item CASCADE;
DROP TABLE IF EXISTS transaction CASCADE;
DROP TABLE IF EXISTS transaction_category CASCADE;
DROP TABLE IF EXISTS message_attachment_mapping CASCADE;
DROP TABLE IF EXISTS attachment CASCADE;
DROP TABLE IF EXISTS signal_message CASCADE;
DROP TABLE IF EXISTS signal_group CASCADE;
DROP TABLE IF EXISTS signal_sender CASCADE;
DROP TABLE IF EXISTS item_category CASCADE;
DROP TABLE IF EXISTS store CASCADE;

-- ============================================================================
-- CRÉATION DES TABLES
-- ============================================================================

-- TABLE 1: STORE
CREATE TABLE store (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    postal_code VARCHAR(20),
    city VARCHAR(100),
    country_code CHAR(2),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_name, city, postal_code)  -- Un magasin unique par nom+ville+code postal
);

-- TABLE 2: SIGNAL_SENDER
CREATE TABLE signal_sender (
    sender_id SERIAL PRIMARY KEY,
    signal_uuid UUID UNIQUE NOT NULL,
    phone_number VARCHAR(50),
    contact_name VARCHAR(255),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 3: SIGNAL_GROUP
CREATE TABLE signal_group (
    group_id SERIAL PRIMARY KEY,
    signal_group_id VARCHAR(255) UNIQUE NOT NULL,
    group_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 4: SIGNAL_MESSAGE
CREATE TABLE signal_message (
    message_id SERIAL PRIMARY KEY,
    sender_id INTEGER,
    group_id INTEGER,
    timestamp TIMESTAMP NOT NULL,
    text_content TEXT,
    is_group_message BOOLEAN DEFAULT FALSE,
    signal_account VARCHAR(255),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender_id) REFERENCES signal_sender(sender_id) ON DELETE SET NULL,
    FOREIGN KEY (group_id) REFERENCES signal_group(group_id) ON DELETE SET NULL
);

-- TABLE 5: ATTACHMENT
CREATE TABLE attachment (
    attachment_id SERIAL PRIMARY KEY,
    signal_attachment_id VARCHAR(255),
    content_type VARCHAR(100),
    filename VARCHAR(255),
    file_size INTEGER,
    upload_timestamp_ms BIGINT,
    file_path TEXT,  -- Peut être NULL si pas encore téléchargé
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 5b: MESSAGE_ATTACHMENT_MAPPING (mapping message -> attachment)
CREATE TABLE message_attachment_mapping (
    message_id INTEGER NOT NULL,
    attachment_id INTEGER NOT NULL,
    PRIMARY KEY (message_id, attachment_id),
    FOREIGN KEY (message_id) REFERENCES signal_message(message_id) ON DELETE CASCADE,
    FOREIGN KEY (attachment_id) REFERENCES attachment(attachment_id) ON DELETE CASCADE
);

-- TABLE 6: TRANSACTION_CATEGORY (catégories de dépenses prédéfinies)
CREATE TABLE transaction_category (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- TABLE 7: TRANSACTION
CREATE TABLE transaction (
    transaction_id SERIAL PRIMARY KEY,
    message_id INTEGER,
    store_id INTEGER NOT NULL,
    transaction_category_id INTEGER,
    receipt_number VARCHAR(100),
    transaction_date DATE NOT NULL,
    transaction_time TIME,
    currency CHAR(3) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store(store_id) ON DELETE RESTRICT,
    FOREIGN KEY (message_id) REFERENCES signal_message(message_id) ON DELETE SET NULL,
    FOREIGN KEY (transaction_category_id) REFERENCES transaction_category(category_id) ON DELETE SET NULL
);

-- TABLE 8: ITEM_CATEGORY (créée avant item car item référence item_category)
CREATE TABLE item_category (
    category_id SERIAL PRIMARY KEY,
    category_main VARCHAR(100) NOT NULL,
    category_sub VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    UNIQUE(category_main, category_sub)
);

-- TABLE 9: ITEM
CREATE TABLE item (
    item_id SERIAL PRIMARY KEY,
    product_name VARCHAR(500) NOT NULL,
    product_reference VARCHAR(100),
    brand VARCHAR(100),
    quantity DECIMAL(10, 3) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    vat_rate VARCHAR(10),
    category_id INTEGER NOT NULL,
    line_number INTEGER,
    FOREIGN KEY (category_id) REFERENCES item_category(category_id) ON DELETE RESTRICT
);

-- TABLE 9b: TRANSACTION_ITEM_MAPPING (mapping transaction -> item)
CREATE TABLE transaction_item_mapping (
    transaction_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    PRIMARY KEY (transaction_id, item_id),
    FOREIGN KEY (transaction_id) REFERENCES transaction(transaction_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES item(item_id) ON DELETE CASCADE
);

-- ============================================================================
-- CRÉATION DES INDEX
-- ============================================================================

-- Store
CREATE INDEX idx_store_name ON store(store_name);
CREATE INDEX idx_store_city ON store(city);
CREATE INDEX idx_store_country ON store(country_code);
CREATE INDEX idx_store_location ON store(store_name, city, postal_code);

-- Signal Sender
CREATE INDEX idx_sender_uuid ON signal_sender(signal_uuid);
CREATE INDEX idx_sender_name ON signal_sender(contact_name);

-- Signal Group
CREATE INDEX idx_group_signal_id ON signal_group(signal_group_id);

-- Signal Message
CREATE INDEX idx_message_timestamp ON signal_message(timestamp);
CREATE INDEX idx_message_processed ON signal_message(processed);
CREATE INDEX idx_message_sender ON signal_message(sender_id);
CREATE INDEX idx_message_group ON signal_message(group_id);

-- Attachment
CREATE INDEX idx_attachment_content_type ON attachment(content_type);
CREATE INDEX idx_attachment_signal_id ON attachment(signal_attachment_id);

-- Message Attachment Mapping
CREATE INDEX idx_msg_att_mapping_message ON message_attachment_mapping(message_id);
CREATE INDEX idx_msg_att_mapping_attachment ON message_attachment_mapping(attachment_id);

-- Transaction Category
CREATE INDEX idx_transaction_category_name ON transaction_category(name);

-- Transaction
CREATE INDEX idx_transaction_store ON transaction(store_id);
CREATE INDEX idx_transaction_message ON transaction(message_id);
CREATE INDEX idx_transaction_category ON transaction(transaction_category_id);
CREATE INDEX idx_transaction_date ON transaction(transaction_date);
CREATE INDEX idx_transaction_currency ON transaction(currency);
CREATE INDEX idx_transaction_date_store ON transaction(transaction_date, store_id);
CREATE INDEX idx_transaction_source ON transaction(source);

-- Transaction Item Mapping
CREATE INDEX idx_trans_item_mapping_transaction ON transaction_item_mapping(transaction_id);
CREATE INDEX idx_trans_item_mapping_item ON transaction_item_mapping(item_id);

-- Item
CREATE INDEX idx_item_category ON item(category_id);
CREATE INDEX idx_item_brand ON item(brand);
CREATE INDEX idx_item_product_name ON item(product_name);

-- Item Category
CREATE INDEX idx_item_category_main ON item_category(category_main);
CREATE INDEX idx_item_category_active ON item_category(active);

SELECT 'Tables et index créés avec succès!' as status;
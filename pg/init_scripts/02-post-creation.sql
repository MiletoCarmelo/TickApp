-- ============================================================================
-- INSERTION DES DONNÉES DE RÉFÉRENCE ET OBJETS DB
-- ============================================================================

-- ============================================================================
-- INSERTION DES CATÉGORIES DE TRANSACTIONS (SPENDS)
-- ============================================================================

INSERT INTO transaction_category (name) VALUES
('carmelo'),
('heather'),
('neon')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- INSERTION DES CATÉGORIES (ITEMS)
-- ============================================================================

INSERT INTO item_category (category_main, category_sub, description) VALUES
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
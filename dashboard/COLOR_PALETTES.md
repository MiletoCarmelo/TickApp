# Guide des couleurs modernes pour TickApp Dashboard

## 🎨 Palette Principale

### Couleurs de base
- **Primary (Bleu)**: `#4F46E5` - Utilisé pour les éléments principaux, boutons, liens
- **Secondary (Cyan)**: `#06B6D4` - Accents, graphiques secondaires
- **Success (Vert)**: `#10B981` - États positifs, confirmations
- **Warning (Orange)**: `#F59E0B` - Alertes, avertissements
- **Danger (Rouge)**: `#EF4444` - Erreurs, actions destructives

### Couleurs de fond
- **Background**: `#F8FAFC` - Fond de page principal
- **Card Background**: `#FFFFFF` - Fond des cards
- **Border**: `#E2E8F0` - Bordures subtiles

### Texte
- **Primary Text**: `#1E293B` - Texte principal
- **Secondary Text**: `#64748B` - Texte secondaire, labels

## 🌈 Palette pour les graphiques

Les catégories utilisent cette palette en rotation :
1. `#4F46E5` (Bleu indigo)
2. `#06B6D4` (Cyan)
3. `#10B981` (Vert émeraude)
4. `#F59E0B` (Orange ambre)
5. `#EF4444` (Rouge)
6. `#8B5CF6` (Violet)

## 📏 Arrondis (Border Radius)

- **Small**: `8px` - Inputs, boutons, badges
- **Medium**: `12px` - Graphiques, composants moyens
- **Large**: `16px` - Cards principales

## 🌑 Ombres (Box Shadow)

### Small
```css
box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
```

### Medium
```css
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
```

### Large
```css
box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
```

## 🎯 Utilisation des couleurs

### Métriques Cards
- **Total dépensé**: Primary (#4F46E5) + bordure top 4px
- **Transactions**: Success (#10B981) + bordure top 4px
- **Moyenne**: Secondary (#06B6D4) + bordure top 4px
- **Magasins**: Warning (#F59E0B) + bordure top 4px

### Graphiques
- **Ligne temporelle**: Primary (#4F46E5) avec fill rgba(79, 70, 229, 0.1)
- **Pie chart**: Rotation de la palette categories
- **Barres horizontales**: Secondary (#06B6D4)

### Table
- **Header**: Background Primary (#4F46E5), texte blanc
- **Lignes impaires**: Background #F8FAFC (50% opacity)
- **Hover**: Background Primary avec 5% opacity

## 💡 Conseils d'utilisation

1. **Cohérence**: Utilise toujours les mêmes couleurs pour les mêmes types d'éléments
2. **Contraste**: Assure un ratio de contraste minimum de 4.5:1 pour le texte
3. **Hiérarchie**: Primary pour l'action principale, Secondary pour les actions secondaires
4. **États**: Success/Warning/Danger pour communiquer l'état des données

## 🔄 Variantes possibles

Si tu veux changer le thème, voici quelques palettes alternatives :

### Thème "Ocean" (Bleu/Vert)
- Primary: `#0EA5E9` (Bleu ciel)
- Secondary: `#14B8A6` (Teal)

### Thème "Sunset" (Orange/Rose)
- Primary: `#F97316` (Orange)
- Secondary: `#EC4899` (Rose)

### Thème "Forest" (Vert/Olive)
- Primary: `#059669` (Vert émeraude)
- Secondary: `#84CC16` (Lime)

### Thème "Corporate" (Bleu foncé/Gris)
- Primary: `#1E40AF` (Bleu foncé)
- Secondary: `#6B7280` (Gris)
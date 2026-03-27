# Journal de bord — Chess FEN Detector

_Dernière mise à jour : 27/03/2026_

## Problèmes rencontrés

- **Images d'entraînement vides (bug SVG)** : les piece sets Lichess injectés dans `chess.svg` n'avaient pas les bons `id` (`white-king`, `black-queen`, etc.), donc les pièces n'apparaissaient pas dans les boards générés. Le modèle s'entraînait sur des cases sans pièces → 56% de précision bloquée. **Solution** : ajout des `id` et `class` corrects dans `load_svg_piece_set()`.
- **Filenames avec `_` dans le nom du piece set** : les styles chess.com (`neo_wood`, `icy_sea`, `8_bit`) causaient un mauvais parsing des labels dans `generate_tiles.py`. **Solution** : extraction de la partie FEN par regex au lieu de split sur `_`.
- **Piece sets `icpieces` et `riohacha` cassés** : scaling SVG incorrect → pièces géantes. **Solution** : supprimés.
- **Piece set `spatial` cassé** : erreur XML "unbound prefix". **Solution** : ignoré (0 boards générés automatiquement).
- **chesscog incompatible avec diagrammes 2D** : détecte bien les échiquiers physiques 3D mais échoue sur les diagrammes de livres ("too many lines"). **Solution** : abandonné au profit de chessboard-recognizer avec MobileNetV2.
- **Preprocessing MobileNetV2** : le modèle recevait des pixels en `[0, 1]` au lieu de `[-1, 1]`. **Solution** : ajout de `applications.mobilenet_v2.preprocess_input()`.
- **TF 2.21 refuse `.tf` pour sauvegarder** : **Solution** : passage à `.keras`.

## Décisions techniques

- **MobileNetV2 au lieu du petit CNN** : le CNN 3 couches (32×32 grayscale) n'a pas la capacité pour 47 styles. MobileNetV2 pré-entraîné (ImageNet) apporte des features visuelles universelles. Raison : meilleur rapport taille/performance (9 Mo).
- **Fine-tuning partiel** : 30 dernières couches dégelées, learning rate 1e-4. Raison : permet au réseau d'adapter ses features aux pièces d'échecs sans casser les poids pré-entraînés.
- **Tiles 96×96 RGB au lieu de 32×32 grayscale** : résolution minimale pour MobileNetV2, et la couleur aide à distinguer pièces noires/blanches. Boards générés en 768×768.
- **Support PNG chess.com** : composition directe (PIL paste avec alpha) au lieu d'injection SVG. Raison : chess.com fournit des PNG, pas des SVG.
- **chesscog abandonné** : pipeline complet (détection board + pièces) mais conçu pour photos 3D, pas diagrammes 2D. Raison : notre cas d'usage principal est les screenshots et diagrammes de livres.

## Avancement

- [x] Diagnostic du problème initial (56% sur multi-styles)
- [x] Exploration de chesscog (installé, testé, abandonné pour diagrammes 2D)
- [x] Remplacement du CNN par MobileNetV2 dans `train.py`
- [x] Fix du bug SVG (pièces manquantes dans les boards générés)
- [x] Support des piece sets chess.com (PNG) dans `generate_local.py`
- [x] Téléchargement de 19 styles chess.com
- [x] Génération de 1 110 boards (28 Lichess + 19 chess.com) × 15 couleurs
- [x] Entraînement réussi : **99.62%** sur 47 styles (71 040 tiles)
- [ ] Intégrer le nouveau modèle dans l'API FastAPI (`chess-fen-detector/backend`)
- [ ] Mettre à jour `recognize.py` pour utiliser le bon preprocessing à l'inférence
- [ ] Tester sur la photo du livre (`test.jpeg`)
- [ ] Ajouter plus de styles si nécessaire (chess24, autres sources)

## Prochaines étapes

1. Mettre à jour `recognize.py` pour le preprocessing MobileNetV2 et la taille 96×96
2. Intégrer le modèle `.keras` dans le backend FastAPI
3. Tester end-to-end sur des images réelles (screenshots + photo du livre)
4. Si besoin, fine-tuner avec des diagrammes de livres d'échecs

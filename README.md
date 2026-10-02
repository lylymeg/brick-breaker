# 🧱 Casse-Briques Retro (Brick Breaker) — PyQt5

Un jeu d'arcade classique de **Casse-Briques** développé en Python avec **PyQt5**. Ce projet met en pratique la physique 2D de base (angles de rebond dynamiques, détection de collisions) et la gestion d'éléments interactifs destructibles avec système de bonus/malus.

---

## 📸 Aperçu du Jeu

- **Interface moderne & Néon** : Rendu graphique 2D personnalisé via `QPainter`.
- **Briques multi-résistances** : Briques nécessitant de 1 à 3 impacts avec indication visuelle de dégradation.
- **Bonus & Malus tombants** : Système de Power-ups générés aléatoirement lors de la destruction des briques.
- **Double mode de contrôle** : Contrôle fluide à la **souris** ou au **clavier**.

---

## 🚀 Fonctionnalités & Concepts Clés

### 🕹️ Mécaniques de jeu
- **Physique de rebond dynamique** : L'angle de renvoi de la balle dépend du point d'impact exact sur la raquette (zone centrale = rebond droit, extrémités = angles aigus).
- **Destructibilité progressive** : Briques de couleurs variées avec résistance graduée (Rouge: 3 coups, Orange: 2 coups, Cyan/Vert: 1 coup).
- **Système de Power-ups (20% de chance d'apparition)** :
  - `↔` **Raquette agrandie** : Augmente la largeur de la raquette.
  - `⚡` **Accélération** : Augmente la vitesse de la balle.
  - `❄` **Ralentissement** : Réduit la vitesse de la balle pour un meilleur contrôle.
  - `♥` **Vie supplémentaire** : Ajoute une vie au compteur.

### 🛠️ Concepts d'apprentissage (PyQt5 & Python)
- **Rendu graphique 2D** : Utilisation de `QPainter`, `QBrush`, `QPen`, et `QRectF`.
- **Boucle de jeu (Game Loop)** : Gestion du rafraîchissement à 60 FPS avec `QTimer`.
- **Gestion des événements** : Capture des mouvements de souris (`mouseMoveEvent`) et touches du clavier (`keyPressEvent` / `keyReleaseEvent`).
- **Détection de collisions AABB** : Traitement des intersections rectangle/cercle pour les murs, la raquette et les briques.

---

## 📋 Prérequis & Installation

### 1. Prérequis
Assurez-vous d'avoir installé **Python 3.8+** sur votre machine.

### 2. Installation de PyQt5
Installez la dépendance PyQt5 via `pip` :

```bash
pip install PyQt5
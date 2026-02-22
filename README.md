# croref
# Empty Image Crop for Blender 4.2+

**Empty Image Crop** est une extension pour Blender qui permet de recadrer visuellement les objets de type **Empty Image** en utilisant des pourcentages, sans modifier physiquement vos fichiers sources originaux.

## ✨ Caractéristiques

- **Recadrage par Pourcentage** : Définissez la largeur et la hauteur du crop (0-100%).
- **Positionnement Flexible** : Ajustez la "fenêtre" de vue sur l'image source.
- **Système de Cache** : Les données d'image sont mises en mémoire pour des ajustements plus rapide après le premier calcul.
- **Synchronisation Automatique** : Détecte si vous changez l'image de l'Empty via l'interface native de Blender et réinitialise les réglages.

## 🚀 Installation

### Via le fichier .zip
1. Téléchargez le fichier `empty_crop_tool.zip` depuis la section [Releases](lien-vers-vos-releases).
2. Dans Blender, allez dans **Edit > Preferences > Get Extensions**.
3. Cliquez sur la petite flèche en haut à droite et choisissez **Install from Disk...**.
4. Sélectionnez le fichier `.zip`.

## 🛠️ Utilisation

1. Ajoutez un objet **Empty** de type **Image** dans votre scène.
2. Allez dans l'onglet **Data** (icône d'image) de l'objet sélectionné.
3. Repérez le panneau **Crop de Référence**.
4. Ajustez vos pourcentages de Crop et de Position.
5. Cliquez sur **Appliquer le Crop** pour générer la version découpée.


## 📜 Licence

Ce projet est sous licence **GPL-3.0-or-later**. Vous êtes libre de le partager et de le modifier.

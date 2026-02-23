Empty Image Crop & Transparency

Français | English

<a name="français"></a>
Français
Présentation

Cet add-on pour Blender permet de recadrer visuellement les objets de type Empty Image et d'appliquer une transparence basée sur une couleur spécifique (Chroma Key). Il est conçu pour faciliter l'utilisation d'images de référence sans modifier les fichiers originaux.
Fonctionnalités

    Recadrage Non-Destructif : L'image d'origine est conservée. L'add-on génère une copie de travail préfixée CR_ pour l'affichage.
    Synchronisation Automatique : Détecte si vous changez l'image de l'Empty via l'interface native de Blender et met à jour la source.
    Mise à jour en temps réel (Auto) : Les modifications de dimensions ou de position sont répercutées sur l'image.
    Transparence par Norme L1​ : Permet de rendre transparente une couleur précise. Le seuil de "Souplesse" utilise la distance L1​ pour une découpe nette.
    Interface Native : Intègre un sélecteur de couleur identique à celui des matériaux de Blender (incluant la pipette).

Utilisation

    Créez un Empty de type Image.

    Rendez-vous dans l'onglet Data (Données de l'objet).

    Utilisez le panneau Crop & Transparence pour ajuster vos réglages.

    Si le mode "Auto" est désactivé, cliquez sur Recadrer pour appliquer les changements.

<a name="english"></a>
English
Overview

This Blender add-on provides tools to visually crop Empty Image objects and apply color-based transparency (Chroma Key). It streamlines the use of reference images by allowing adjustments directly within the 3D view properties.
Features

    Non-Destructive Cropping: The source image remains untouched. The add-on creates a working copy prefixed with CR_ for display.
    Automatic Sync: Automatically detects image changes on the Empty object via Blender's native interface and updates the source pointer.
    Real-time Updates (Auto) : Dimension and position adjustments are reflected on the cropped image.
    L1​ Norm Transparency: Remove specific background colors. The "Threshold" slider uses L1​ distance for precise control over the keyed area.
    Native UI: Features a standard Blender color picker (including the eyedropper tool) for an integrated experience.

How to use

    Create an Empty set to Image display type.

    Navigate to the Data tab in the Properties panel.

    Use the Crop & Transparency panel to adjust settings.

    If "Auto" mode is off, click Recadrer (Crop) to manually update the result.

Spécifications techniques / Technical Specs

    Calculs / Computation : NumPy.

    Compatibilité : Blender 4.2+.

    Performance : Utilise un système de cache (PIXEL_CACHE) pour éviter de relire les données de l'image source à chaque modification.

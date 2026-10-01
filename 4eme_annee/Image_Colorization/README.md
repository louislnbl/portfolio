# Image Colorization

## Introduction

Dans le cadre de notre quatrième année à l’INSA Rouen Normandie, nous avons réalisé un projet de **deep learning** en équipe de trois.

Le projet sur lequel nous avons travaillé visait à **coloriser automatiquement des images en noir et blanc**. Pour cela, nous avons entraîné un **GAN conditionnel de type Pix2Pix** : un générateur U-Net prédit les couleurs d’une image à partir de sa luminance, tandis qu’un discriminateur PatchGAN juge localement le réalisme du résultat.

Les entraînements ont été réalisés sur le supercalculateur **Arctic** du CRIANN.

---

## But du projet

- Comprendre et implémenter une **architecture GAN conditionnelle** (générateur U-Net, discriminateur PatchGAN).
- Mettre en place une **chaîne d’entraînement complète** : préparation des données, augmentation, entraînement, suivi et évaluation.
- **Étudier l’influence des choix d’entraînement** : taux d’apprentissage, pondération de la perte L1, ajout d’une perceptual loss.
- Apprendre à **utiliser un supercalculateur** pour entraîner un modèle sur GPU.

---

## Compétences développées

- **Deep learning avec PyTorch** : réseaux convolutifs, entraînement adversarial, fonctions de perte combinées.
- **Traitement d’images** : espace colorimétrique Lab, normalisation et augmentation de données.
- **Calcul sur supercalculateur** : soumission de jobs avec Slurm, entraînement sur GPU.
- **Suivi d’expériences** avec TensorBoard et **évaluation** par des métriques adaptées (MAE, précision par pixel).
- **Travail collaboratif** via Git et GitLab.

---

## Contenu du dossier

- [`/code`](./code) — Code du projet (modèles, jeu de données, entraînement, évaluation). La présentation détaillée et le mode d’emploi sur Arctic se trouvent dans [`code/README.md`](./code/README.md).
- [`/presentation`](./presentation) — Support de présentation (sources LaTeX et PDF).

Les données (dataset Flowers de Kaggle) et les poids des modèles entraînés ne sont pas versionnés.

---

> *Année universitaire : 2025 – 2026*  
> *Auteur : LENOBLE Louis*  
> *ITI4 – Deuxième Année de spécialisation*

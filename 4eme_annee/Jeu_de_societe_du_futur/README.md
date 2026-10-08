# Jeu de société du futur

## Introduction

Dans le cadre de notre quatrième année à l’INSA Rouen Normandie, nous avons réalisé en équipe un **Projet d’Approfondissement et d’Ouverture (PAO)**.

Le projet sur lequel nous avons travaillé, le jeu **« Brain Strom »**, visait à imaginer un jeu de société mêlant un plateau physique et le numérique. Les joueurs se retrouvent dans une partie en ligne depuis le navigateur de leur téléphone, dont la caméra filme le plateau : les pièces portent des **marqueurs ArUco** qui sont détectés en temps réel par traitement d’image.

---

## But du projet

- **Construire un projet de bout en bout** : faire naître une idée, faire émerger des solutions et les mettre en place.
- Développer une **application web temps réel** accessible depuis un téléphone, sans installation.
- Mettre en place un **traitement d’image** capable de reconnaître les éléments du plateau à partir du flux de la caméra.
- **Concevoir et imprimer en 3D** les pièces du plateau.

---

## Compétences développées

- **Développement web** : HTML, CSS, JavaScript, serveur Node.js avec Express.
- **Communication temps réel** entre les joueurs grâce à Socket.IO (création de parties, synchronisation de l’état du jeu).
- **Traitement d’image avec OpenCV** : détection de marqueurs ArUco dans un service Python (Flask).
- **Architecture en deux services** : serveur Node.js relayant les images à un service Python par HTTP.
- **Modélisation 3D** des pièces du plateau.
- **Travail en équipe** et gestion de projet via Git et GitLab.

---

## Contenu du dossier

- [`/code`](./code) : Application web et service de traitement d’image. Les instructions d’installation et de lancement se trouvent dans [`code/README.md`](./code/README.md).
- [`/plans_plateau`](./plans_plateau) : Modèles 3D (STL) des pièces du plateau.

---

> *Année universitaire : 2025 - 2026*  
> *Auteur : LENOBLE Louis*  
> *ITI4 - Deuxième Année de spécialisation*

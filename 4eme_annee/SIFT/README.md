# SIFT

## Introduction

Dans le cadre de notre quatrième année à l’INSA Rouen Normandie, nous avons réalisé un projet en équipe de quatre pour le cours de **Traitement d’Image (TIM)**.

Le projet sur lequel nous avons travaillé portait sur l’algorithme **SIFT** (*Scale-Invariant Feature Transform*), proposé par David G. Lowe en 2004. Cette méthode extrait d’une image des points d’intérêt invariants à l’échelle et à la rotation, ce qui permet de mettre en correspondance deux images d’une même scène malgré un changement de point de vue.

L’enjeu était d’étudier la méthode en détail, d’en proposer notre propre implémentation, puis de la mettre en œuvre sur des cas concrets.

---

## But du projet

- Comprendre et présenter les **quatre étapes de SIFT** : détection des extremums dans l’espace des échelles, localisation des points clés, assignation d’orientation et création des descripteurs.
- **Implémenter l’algorithme en Python** et comparer nos résultats à ceux d’OpenCV.
- Mettre en œuvre SIFT sur des **applications concrètes** : localisation d’un objet dans une scène, assemblage de panorama et recherche d’images.
- Développer un **esprit critique** sur les limites de la méthode.

---

## Compétences développées

- **Traitement d’images** : espace des échelles, différences de gaussiennes, gradients et histogrammes d’orientation.
- **Mise en correspondance d’images** : appariement de descripteurs, estimation d’homographie.
- **Utilisation d’outils Python scientifiques** : NumPy, OpenCV, Matplotlib, Jupyter Notebook.
- **Rédaction scientifique** : rapport et support de présentation en LaTeX à partir d’un article de recherche.
- **Travail collaboratif** via Git et GitLab.

---

## Contenu du dossier

- [`/implementation`](./implementation) : Notre implémentation de SIFT, étape par étape, comparée à celle d’OpenCV (Jupyter Notebook).
- [`/application`](./application) : Applications de SIFT à la détection d’objet, au panorama et à la recherche d’images (Jupyter Notebook).
- [`/rapport`](./rapport) : Sources LaTeX du rapport, dont la version compilée est [`rapport.pdf`](./rapport.pdf).
- [`/presentation`](./presentation) : Support de présentation (sources LaTeX et PDF).

---

## Références

- D. G. Lowe, *Distinctive Image Features from Scale-Invariant Keypoints*, International Journal of Computer Vision, 2004.
- [Scale-invariant feature transform (Wikipédia)](https://fr.wikipedia.org/wiki/Scale-invariant_feature_transform)
- [Documentation OpenCV : Introduction to SIFT](https://docs.opencv.org/4.x/da/df5/tutorial_py_sift_intro.html)
- [PythonSIFT (R. Islam)](https://github.com/rmislam/PythonSIFT/blob/master/pysift.py) et l’[article associé](https://medium.com/@russmislam/implementing-sift-in-python-a-complete-guide-part-1-306a99b50aa5)
- [What is SIFT? (Roboflow)](https://blog.roboflow.com/sift/)

---

> *Année universitaire : 2025 - 2026*  
> *Auteur : LENOBLE Louis*  
> *ITI4 - Deuxième Année de spécialisation*

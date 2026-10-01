"""
Jeu de données pour charger des images en .npy (espace colorimétrique L*a*b*).
"""

import os
import torch
from torch.utils.data import Dataset
import numpy as np


class NPYImageDataset(Dataset):
    """
    Jeu de données pour charger des images stockées en .npy.

    Ce dataset attend des fichiers .npy contenant des images en espace L*a*b*
    de forme (H, W, 3). Il sépare le canal de luminance (L) et les canaux
    de chrominance (ab) pour préparer les tenseurs pour PyTorch.

    Args:
        root_dir (str): Répertoire contenant tous les fichiers .npy.
        file_list (list): Liste des fichiers à charger.
        transform (callable, optional): Transformation optionnelle appliquée.
    """

    def __init__(self, root_dir, file_list=None, transform=None):
        """
        Initialise le dataset avec le répertoire et la liste de fichiers.

        Args:
            root_dir (str): Chemin vers le répertoire contenant les .npy.
            file_list (list, optional): Liste de fichiers spécifiques à charger.
                Si None, charge tous les .npy du répertoire.
            transform (callable, optional): Transformation optionnelle.
        """
        self.root_dir = root_dir
        self.transform = transform
        
        if file_list is None:
            all_files = os.listdir(root_dir)
            self.file_list = [f for f in all_files if f.endswith('.npy')]
        else:
            self.file_list = file_list
        
        if len(self.file_list) == 0:
            raise ValueError(f"No .npy files found in {root_dir}")

    def __len__(self):
        """Retourne le nombre total d'échantillons."""
        return len(self.file_list)

    def __getitem__(self, idx):
        """
        Récupère une paire d'images (canal L, canaux ab) à l'index donné.

        Args:
            idx (int): Index de l'échantillon à récupérer.

        Returns:
            tuple: (gray, ab) où :
                - gray: Tensor de forme (1, H, W) contenant le canal L
                - ab: Tensor de forme (2, H, W) contenant les canaux ab
        """
        img_path = os.path.join(self.root_dir, self.file_list[idx])
        img_lab = np.load(img_path)  # Shape: (H, W, 3) en L*a*b*
        
        L_channel = img_lab[:, :, 0:1]  # Shape: (H, W, 1)
        ab_channels = img_lab[:, :, 1:3]  # Shape: (H, W, 2)
        
        gray = torch.from_numpy(L_channel).permute(2, 0, 1).float()
        ab = torch.from_numpy(ab_channels).permute(2, 0, 1).float()
        
        gray = gray / 128.0 - 1.0          # Normalisation L
        ab = (ab - 128.0) / 128.0          # Normalisation ab
        
        if self.transform:
            gray = self.transform(gray)
            ab = self.transform(ab)
        
        return gray, ab


def get_dataloader(data_dir, batch_size, num_workers=4, shuffle=True):
    """
    Crée un DataLoader pour un répertoire donné.
    
    Args:
        data_dir (str): Chemin vers le répertoire contenant les fichiers .npy
        batch_size (int): Taille des batchs
        num_workers (int): Nombre de workers pour le chargement
        shuffle (bool): Mélanger les données
        
    Returns:
        DataLoader: DataLoader configuré
    """
    dataset = NPYImageDataset(root_dir=data_dir)
    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True  # Accélère le transfert GPU
    )
    return dataloader

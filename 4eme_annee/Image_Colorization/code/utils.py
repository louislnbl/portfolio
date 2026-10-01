"""
Fonctions utilitaires pour le training, checkpointing, et logging
"""

import os
import yaml
import torch
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import torchvision.utils as vutils


def load_config(config_path):
    """
    Charge un fichier de configuration YAML.
    
    Args:
        config_path (str): Chemin vers le fichier YAML
        
    Returns:
        dict: Configuration chargée
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def save_config(config, save_path):
    """
    Sauvegarde la configuration dans un fichier YAML.
    
    Args:
        config (dict): Configuration à sauvegarder
        save_path (str): Chemin de sauvegarde
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def set_seed(seed):
    """
    Fixe les seeds pour la reproductibilité.
    
    Args:
        seed (int): Valeur du seed
    """
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class CheckpointManager:
    """
    Gère la sauvegarde et le chargement des checkpoints.
    Conserve uniquement le meilleur modèle basé sur une métrique.
    """
    
    def __init__(self, checkpoint_dir, metric_name='val_loss_G', mode='min'):
        """
        Args:
            checkpoint_dir (str): Répertoire pour sauvegarder les checkpoints
            metric_name (str): Nom de la métrique à surveiller
            mode (str): 'min' ou 'max' selon qu'on veut minimiser ou maximiser
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.metric_name = metric_name
        self.mode = mode
        self.best_metric = float('inf') if mode == 'min' else float('-inf')
        self.best_checkpoint_path = None
        
    def is_better(self, metric_value):
        """
        Vérifie si la métrique actuelle est meilleure que la précédente.
        
        Args:
            metric_value (float): Valeur actuelle de la métrique
            
        Returns:
            bool: True si meilleure, False sinon
        """
        if self.mode == 'min':
            return metric_value < self.best_metric
        else:
            return metric_value > self.best_metric
    
    def save_checkpoint(self, state, metric_value, epoch):
        """
        Sauvegarde un checkpoint si la métrique s'est améliorée.
        
        Args:
            state (dict): État à sauvegarder (modèles, optimizers, etc.)
            metric_value (float): Valeur de la métrique
            epoch (int): Numéro de l'epoch
            
        Returns:
            bool: True si sauvegardé, False sinon
        """
        if self.is_better(metric_value):
            # Supprimer l'ancien meilleur checkpoint
            if self.best_checkpoint_path and self.best_checkpoint_path.exists():
                self.best_checkpoint_path.unlink()
            
            # Sauvegarder le nouveau meilleur
            self.best_metric = metric_value
            self.best_checkpoint_path = self.checkpoint_dir / f"best_epoch{epoch:03d}_{self.metric_name}_{metric_value:.4f}.pt"
            torch.save(state, self.best_checkpoint_path)
            
            print(f"  ✓ Nouveau meilleur modèle sauvegardé: {self.metric_name}={metric_value:.4f}")
            return True
        return False
    
    def load_checkpoint(self, checkpoint_path, generator, discriminator,
                        optimizer_G=None, optimizer_D=None):
        """
        Charge un checkpoint.
        
        Args:
            checkpoint_path (str): Chemin vers le checkpoint
            generator (nn.Module): Modèle générateur
            discriminator (nn.Module): Modèle discriminateur
            optimizer_G (Optimizer, optional): Optimizer du générateur
            optimizer_D (Optimizer, optional): Optimizer du discriminateur
            
        Returns:
            int: Numéro de l'epoch du checkpoint
        """
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint non trouvé: {checkpoint_path}")
        
        checkpoint = torch.load(checkpoint_path)
        
        generator.load_state_dict(checkpoint['generator'])
        discriminator.load_state_dict(checkpoint['discriminator'])
        
        if optimizer_G is not None and 'optimizer_G' in checkpoint:
            optimizer_G.load_state_dict(checkpoint['optimizer_G'])
        
        if optimizer_D is not None and 'optimizer_D' in checkpoint:
            optimizer_D.load_state_dict(checkpoint['optimizer_D'])
        
        epoch = checkpoint.get('epoch', 0)
        print(f"Checkpoint chargé depuis l'epoch {epoch}")
        
        return epoch


class MetricsLogger:
    """
    Logger pour suivre les métriques d'entraînement.
    """
    
    def __init__(self):
        """Initialise les conteneurs de métriques."""
        self.metrics = {
            'train_loss_D': [],
            'train_loss_G': [],
            'val_loss_D': [],
            'val_loss_G': [],
            'lr_G': [],
            'lr_D': []
        }
    
    def log(self, **kwargs):
        """
        Enregistre des métriques.
        
        Args:
            **kwargs: Paires clé-valeur des métriques
        """
        for key, value in kwargs.items():
            if key in self.metrics:
                self.metrics[key].append(value)
    
    def get_history(self):
        """Retourne l'historique complet."""
        return self.metrics


def save_validation_images(generator, val_dataloader, device, save_dir, epoch, num_images=4):
    """
    Génère et sauvegarde des images de validation pour visualiser la progression.
    Convertit correctement L*a*b* → RGB pour affichage.
    
    Args:
        generator (nn.Module): Modèle générateur
        val_dataloader (DataLoader): DataLoader de validation
        device (torch.device): Device utilisé
        save_dir (str): Répertoire de sauvegarde
        epoch (int): Numéro de l'epoch
        num_images (int): Nombre d'images à sauvegarder
    """
    try:
        import cv2
        
        generator.eval()
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        gray, real_ab = next(iter(val_dataloader))
        gray = gray[:num_images].to(device)
        real_ab = real_ab[:num_images].to(device)
        
        with torch.no_grad():
            fake_ab = generator(gray)
        
        gray_np = gray.cpu().numpy()    
        real_ab_np = real_ab.cpu().numpy()  
        fake_ab_np = fake_ab.cpu().numpy() 
        
        fig, axes = plt.subplots(num_images, 3, figsize=(12, 4 * num_images))
        if num_images == 1:
            axes = axes[np.newaxis, :]
        
        for i in range(num_images):
            gray_img = gray_np[i].transpose(1, 2, 0)      # (H, W, 1)
            real_ab_img = real_ab_np[i].transpose(1, 2, 0)  # (H, W, 2)
            fake_ab_img = fake_ab_np[i].transpose(1, 2, 0)  # (H, W, 2)
            
            gray_img = (gray_img + 1.0) * 128.0
            
            real_ab_img = real_ab_img * 128.0 + 128.0
            fake_ab_img = fake_ab_img * 128.0 + 128.0
            
            real_lab = np.concatenate([gray_img, real_ab_img], axis=-1)  # (H, W, 3)
            fake_lab = np.concatenate([gray_img, fake_ab_img], axis=-1)  # (H, W, 3)
            
            gray_img_uint8 = gray_img.astype(np.uint8)
            real_lab_uint8 = real_lab.astype(np.uint8)
            fake_lab_uint8 = fake_lab.astype(np.uint8)
            
            real_bgr = cv2.cvtColor(real_lab_uint8, cv2.COLOR_LAB2BGR)
            fake_bgr = cv2.cvtColor(fake_lab_uint8, cv2.COLOR_LAB2BGR)
            
            axes[i, 0].imshow(gray_img_uint8[:, :, 0], cmap='gray')
            axes[i, 0].set_title('Input (L channel)')
            axes[i, 0].axis('off')
            
            axes[i, 1].imshow(real_bgr)
            axes[i, 1].set_title('Ground Truth')
            axes[i, 1].axis('off')
            
            axes[i, 2].imshow(fake_bgr)
            axes[i, 2].set_title('Generated')
            axes[i, 2].axis('off')
        
        plt.tight_layout()
        save_path = save_dir / f'validation_epoch{epoch:03d}.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        generator.train()
        
    except Exception as e:
        print(f"  ⚠ Erreur lors de la sauvegarde des images: {e}")
        import traceback
        traceback.print_exc()


def count_parameters(model):
    """
    Compte le nombre de paramètres entraînables d'un modèle.
    
    Args:
        model (nn.Module): Modèle PyTorch
        
    Returns:
        int: Nombre de paramètres
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def format_time(seconds):
    """
    Formate un temps en secondes en format lisible.
    
    Args:
        seconds (float): Temps en secondes
        
    Returns:
        str: Temps formaté (ex: "1h 23m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

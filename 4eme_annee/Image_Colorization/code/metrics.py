"""
Script pour calculer les métriques du GAN de colorisation d'images
"""
import torch

def compute_mae(fake_ab, real_ab):
    """
    Calcule la Mean Absolute Error standard entre -1 et 1.
    """
    return torch.mean(torch.abs(fake_ab - real_ab)).item()

def compute_color_accuracy(fake_ab, real_ab, threshold=5.0):
    """
    Calcule le % de pixels dont la distance euclidienne en Lab est < seuil.
    """

    dist = torch.sqrt(torch.sum((fake_ab - real_ab) ** 2, dim=1))
    
    correct_pixels = (dist < (threshold / 110.0)).float() 
    
    return torch.mean(correct_pixels).item()
"""
Script pour calculer la Perceptual Loss
"""

from torchvision import models
import torch

class VGGPerceptualLoss(torch.nn.Module):
    """
    Calcule la Perceptual Loss en utilisant VGG16 pré-entraîné sur ImageNet.
    Utilise les activations des couches 1 et 2 du réseau.
    """
    def __init__(self):
        """
        Initialise le modèle VGG16 et les couches de slicing.
        """
        super().__init__()
        # On prend les premières couches de VGG16 (pré-entraîné sur ImageNet)
        vgg = models.vgg16(weights='IMAGENET1K_V1').features
        # Couches de bas niveau
        self.slice1 = torch.nn.Sequential(*list(vgg.children())[:4])
        # Couches de textures
        self.slice2 = torch.nn.Sequential(*list(vgg.children())[4:9])
        # On ne veut pas entraîner VGG
        for param in self.parameters():
            param.requires_grad = False 
        self.eval()

    def forward(self, input, target):
        """
        Args:
            input (torch.Tensor): Image générée (L+a+b)
            target (torch.Tensor): Image réelle (L+a+b)

        Returns:
            torch.Tensor: Perceptual Loss
        """
        # Passage dans le premier bloc
        h1_vrai = self.slice1(target)
        h1_fake = self.slice1(input)

        # Passage du RÉSULTAT du bloc 1 dans le bloc 2
        h2_vrai = self.slice2(h1_vrai)
        h2_fake = self.slice2(h1_fake)

        loss = torch.nn.functional.l1_loss(h1_fake, h1_vrai) + \
            torch.nn.functional.l1_loss(h2_fake, h2_vrai)
        return loss

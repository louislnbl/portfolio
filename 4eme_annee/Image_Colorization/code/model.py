"""
Architectures du générateur (U-Net) et du discriminateur (PatchGAN)
pour la colorisation d'images avec un GAN.
"""

import torch
import torch.nn as nn


class Generator(nn.Module):
    """
    Générateur basé sur U-Net pour la colorisation d'images.

    Le générateur prend un canal de luminance (L) et prédit les canaux (ab).
    Il utilise une architecture encodeur-décodeur avec des skip connections
    (U-Net) pour préserver l'information spatiale de l'entrée.
    """

    def __init__(self):
        """Initialise les couches du générateur (encodeur et décodeur)."""
        super().__init__()

        # ── Encodeur ────────────────────────────────────────────────────────
        self.enc1 = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1, bias=True),
            nn.LeakyReLU(0.2, inplace=True)
        )
        self.enc2 = self._enc(64, 64, stride=2)
        self.enc3 = self._enc(64, 128, stride=2)
        self.enc4 = self._enc(128, 256, stride=2)
        self.enc5 = self._enc(256, 512, stride=2)
        self.enc6 = self._enc(512, 512, stride=2)
        self.enc7 = self._enc(512, 512, stride=2)
        self.enc8 = self._enc(512, 512, stride=2)

        # ── Decodeur ────────────────────────────────────────────────────────
        self.dec1 = self._dec(512, 512, dropout=0.5)
        self.dec2 = self._dec(1024, 512, dropout=0.5)
        self.dec3 = self._dec(1024, 512, dropout=0.5)
        self.dec4 = self._dec(1024, 256, dropout=0.0)
        self.dec5 = self._dec(512, 128, dropout=0.0)
        self.dec6 = self._dec(256, 64, dropout=0.0)
        self.dec7 = self._dec(128, 64, dropout=0.0)
        
        self.final = nn.Sequential(
            nn.Conv2d(128, 2, kernel_size=1, stride=1, padding=0),
            nn.Tanh()
        )

    def _enc(self, in_ch, out_ch, stride):
        """
        Méthode utilitaire pour créer un bloc encodeur.

        Args:
            in_ch (int): Nombre de canaux d'entrée
            out_ch (int): Nombre de canaux de sortie
            stride (int): Stride de la convolution

        Returns:
            nn.Sequential: Bloc encodeur
        """
        return nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=4, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.LeakyReLU(0.2, inplace=True)
        )

    def _dec(self, in_ch, out_ch, dropout):
        """
        Méthode utilitaire pour créer un bloc décodeur.

        Args:
            in_ch (int): Nombre de canaux d'entrée
            out_ch (int): Nombre de canaux de sortie
            dropout (float): Probabilité de dropout (0.0 = pas de dropout)

        Returns:
            nn.Sequential: Bloc décodeur
        """
        layers = [
            nn.ConvTranspose2d(in_ch, out_ch, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        ]
        if dropout > 0:
            layers.append(nn.Dropout(dropout))
        return nn.Sequential(*layers)

    def forward(self, x):
        """
        Passage avant (forward) du générateur U-Net.

        Args:
            x (Tensor): Image en niveaux de gris (canal L), forme (B, 1, H, W)

        Returns:
            Tensor: Canaux ab prédits, forme (B, 2, H, W)
        """
        # ── Encodeur ──────────────────────────────────
        e1 = self.enc1(x)      # (B, 64, H, W)
        e2 = self.enc2(e1)     # (B, 64, H/2, W/2)
        e3 = self.enc3(e2)     # (B, 128, H/4, W/4)
        e4 = self.enc4(e3)     # (B, 256, H/8, W/8)
        e5 = self.enc5(e4)     # (B, 512, H/16, W/16)
        e6 = self.enc6(e5)     # (B, 512, H/32, W/32)
        e7 = self.enc7(e6)     # (B, 512, H/64, W/64)
        e8 = self.enc8(e7)     # (B, 512, H/128, W/128)

        # ── Decodeur ────────────────────────────────────────────────────────
        d1 = self.dec1(e8)                      # (B, 512, H/64, W/64)
        d2 = self.dec2(torch.cat([d1, e7], 1))  # (B, 512, H/32, W/32)
        d3 = self.dec3(torch.cat([d2, e6], 1))  # (B, 512, H/16, W/16)
        d4 = self.dec4(torch.cat([d3, e5], 1))  # (B, 512, H/8, W/8)
        d5 = self.dec5(torch.cat([d4, e4], 1))  # (B, 256, H/4, W/4)
        d6 = self.dec6(torch.cat([d5, e3], 1))  # (B, 128, H/2, W/2)
        d7 = self.dec7(torch.cat([d6, e2], 1))  # (B, 64, H, W)
        
        out = self.final(torch.cat([d7, e1], 1))  # (B, 2, H, W)
        
        return out


class Discriminator(nn.Module):
    """
    Discriminateur PatchGAN pour déterminer si une paire d'images est réelle ou fausse.

    Ce discriminateur classe des patches N x N en réel ou faux, ce qui encourage
    le générateur à produire des détails haute fréquence.
    """

    def __init__(self):
        """Initialise le discriminateur avec une suite de blocs convolutionnels."""
        super().__init__()

        self.disc = nn.Sequential(
            self._block(3, 64, batchnorm=False),
            self._block(64, 128),
            self._block(128, 256),
            self._block(256, 512),
            nn.Conv2d(512, 1, kernel_size=4, stride=1, padding=1),
            nn.Sigmoid()
        )

    def _block(self, in_ch, out_ch, batchnorm=True):
        """
        Méthode utilitaire pour créer un bloc du discriminateur.

        Args:
            in_ch (int): Nombre de canaux d'entrée.
            out_ch (int): Nombre de canaux de sortie.
            batchnorm (bool): Ajoute ou non la batch normalization.

        Returns:
            nn.Sequential: Bloc du discriminateur.
        """
        layers = [
            nn.Conv2d(in_ch, out_ch, kernel_size=4, stride=2, padding=1, bias=False)
        ]
        if batchnorm:
            layers.append(nn.BatchNorm2d(out_ch))
        layers.append(nn.LeakyReLU(0.2, inplace=True))
        
        return nn.Sequential(*layers)

    def forward(self, gray, ab):
        """
        Passage avant (forward) du discriminateur.

        Args:
            gray (Tensor): Entrée en niveaux de gris (canal L), forme (B, 1, H, W)
            ab (Tensor): Canaux couleur (ab), forme (B, 2, H, W)

        Returns:
            Tensor: Sortie du discriminateur (patches), forme (B, 1, H', W')
        """
        x = torch.cat([gray, ab], dim=1)
        return self.disc(x)


def initialize_weights(model):
    """
    Initialise les poids du modèle selon la méthode recommandée pour les GANs.
    
    Args:
        model (nn.Module): Modèle à initialiser
    """
    for m in model.modules():
        if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d)):
            nn.init.normal_(m.weight, 0.0, 0.02)
        elif isinstance(m, nn.BatchNorm2d):
            nn.init.normal_(m.weight, 1.0, 0.02)
            nn.init.constant_(m.bias, 0)

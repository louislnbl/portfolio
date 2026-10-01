#!/usr/bin/env python3
"""
Script d'entraînement pour le GAN de colorisation d'images.
Usage: python train.py
"""

import os
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from model import Generator, Discriminator, initialize_weights
from dataset import get_dataloader
from utils import (
    load_config, save_config, set_seed, CheckpointManager, 
    MetricsLogger, save_validation_images, count_parameters, format_time
)
from perceptual_loss import VGGPerceptualLoss
from metrics import compute_mae, compute_color_accuracy


def train_one_epoch(generator, discriminator, dataloader, optimizer_G, optimizer_D,
                    criterion_GAN, criterion_L1, lambda_l1, device, pbar=None, lambda_vgg=10.0, criterion_perceptual=None):
    """
    Entraîne le GAN pendant une epoch.
    
    Args:
        generator (nn.Module): Générateur
        discriminator (nn.Module): Discriminateur
        dataloader (DataLoader): DataLoader d'entraînement
        optimizer_G (Optimizer): Optimizer du générateur
        optimizer_D (Optimizer): Optimizer du discriminateur
        criterion_GAN (Loss): Loss adversariale (BCELoss)
        criterion_L1 (Loss): Loss L1
        lambda_l1 (float): Poids de la loss L1
        device (torch.device): Device
        pbar (tqdm, optional): Barre de progression
        
    Returns:
        tuple: (avg_loss_D, avg_loss_G)
    """
    generator.train()
    discriminator.train()
    
    total_loss_D = 0.0
    total_loss_G = 0.0
    n_batches = 0
    
    for gray, real_ab in dataloader:
        batch_size = gray.size(0)
        gray = gray.to(device)
        real_ab = real_ab.to(device)
        
        # ═══════════════════════════════════════════════════════════════════
        #Entraînement du Discriminateur
        # ═══════════════════════════════════════════════════════════════════
        optimizer_D.zero_grad()
        
        # Prédictions sur les vraies images
        pred_real = discriminator(gray, real_ab)
        real_labels = torch.ones_like(pred_real)
        loss_D_real = criterion_GAN(pred_real, real_labels)
        
        # Prédictions sur les fausses images
        fake_ab = generator(gray)
        pred_fake = discriminator(gray, fake_ab.detach())
        fake_labels = torch.zeros_like(pred_fake)
        loss_D_fake = criterion_GAN(pred_fake, fake_labels)
        
        # Loss totale du discriminateur
        loss_D = (loss_D_real + loss_D_fake) * 0.5
        loss_D.backward()
        optimizer_D.step()
        
        # ═══════════════════════════════════════════════════════════════════
        # Entraînement du Générateur
        # ═══════════════════════════════════════════════════════════════════
        optimizer_G.zero_grad()
        
        optimizer_G.zero_grad()
        
        # 1. Loss adversariale
        pred_fake = discriminator(gray, fake_ab)
        labels_vrai_pour_G = torch.ones_like(pred_fake)
        loss_G_GAN = criterion_GAN(pred_fake, labels_vrai_pour_G)

        # 2. Loss L1 Pondérée (Fidélité pixel par pixel)
        diff_abs = torch.abs(fake_ab - real_ab)
        saturation = torch.norm(real_ab, dim=1, keepdim=True) 
        poids_spatial = 1.0 + 6.0 * saturation 
        loss_G_L1 = (diff_abs * poids_spatial).mean()

        # 3. La Perceptual Loss
        fake_rgb = torch.cat([gray, fake_ab], dim=1) 
        real_rgb = torch.cat([gray, real_ab], dim=1)
        loss_vgg = criterion_perceptual(fake_rgb, real_rgb)

        # 4. Combinaison
        loss_G = loss_G_GAN + (lambda_l1 * loss_G_L1) + (lambda_vgg * loss_vgg)
        
        loss_G.backward()
        optimizer_G.step()
        
        # Accumuler les losses
        total_loss_D += loss_D.item()
        total_loss_G += loss_G.item()
        n_batches += 1
        
        # Mettre à jour la barre de progression
        if pbar is not None:
            pbar.set_postfix({
                'loss_D': f'{loss_D.item():.4f}',
                'loss_G': f'{loss_G.item():.4f}'
            })
            pbar.update(1)
    
    avg_loss_D = total_loss_D / n_batches
    avg_loss_G = total_loss_G / n_batches
    
    return avg_loss_D, avg_loss_G


def validate(generator, discriminator, val_dataloader, criterion_GAN, 
            criterion_L1, lambda_l1, device):
    """
    Évalue le modèle sur le set de validation.
    
    Args:
        generator (nn.Module): Générateur
        discriminator (nn.Module): Discriminateur
        val_dataloader (DataLoader): DataLoader de validation
        criterion_GAN (Loss): Loss adversariale
        criterion_L1 (Loss): Loss L1
        lambda_l1 (float): Poids de la loss L1
        device (torch.device): Device
        
    Returns:
        tuple: (val_loss_D, val_loss_G, val_acc, val_mae)
    """
    generator.eval()
    discriminator.eval()
    
    total_loss_D = 0.0
    total_loss_G = 0.0
    total_mae = 0.0
    total_acc = 0.0
    n_batches = 0
    
    with torch.no_grad():
        for gray, real_ab in val_dataloader:
            batch_size = gray.size(0)
            gray = gray.to(device)
            real_ab = real_ab.to(device)
            
            # Discriminateur
            pred_real = discriminator(gray, real_ab)
            real_labels = torch.ones_like(pred_real)
            loss_D_real = criterion_GAN(pred_real, real_labels)
            
            fake_ab = generator(gray)
            pred_fake = discriminator(gray, fake_ab)
            fake_labels = torch.zeros_like(pred_fake)
            loss_D_fake = criterion_GAN(pred_fake, fake_labels)
            
            loss_D = (loss_D_real + loss_D_fake) * 0.5
            
            # Générateur
            labels_vrai_pour_G = torch.ones_like(pred_fake)
            loss_G_GAN = criterion_GAN(pred_fake, labels_vrai_pour_G)
            loss_G_L1 = criterion_L1(fake_ab, real_ab)
            loss_G = loss_G_GAN + lambda_l1 * loss_G_L1
            
            total_loss_D += loss_D.item()
            total_loss_G += loss_G.item()

            total_mae += compute_mae(fake_ab, real_ab)
            total_acc += compute_color_accuracy(fake_ab, real_ab)

            n_batches += 1

    val_loss_D = total_loss_D / n_batches
    val_loss_G = total_loss_G / n_batches
    avg_mae = total_mae / n_batches
    avg_acc = total_acc / n_batches
    
    return val_loss_D, val_loss_G,avg_mae, avg_acc


def main():
    """Point d'entrée principal : charge la config et lance l'entraînement."""
    # ═══════════════════════════════════════════════════════════════════════
    # Configuration et setup
    # ═══════════════════════════════════════════════════════════════════════
    config = load_config('config.yaml')
    
    set_seed(config['seed'])
    
    device = torch.device(config['device'] if torch.cuda.is_available() else 'cpu')
    print(f"\n{'='*70}")
    print(f"[INFO] Démarrage de l'entraînement")
    print(f"{'='*70}")
    print(f"[INFO] Device: {device}")
    if torch.cuda.is_available():
        print(f"[INFO] GPU: {torch.cuda.get_device_name(0)}")
        print(f"[INFO] CUDA Version: {torch.version.cuda}")

    # ═══════════════════════════════════════════════════════════════════════
    # DataLoaders
    # ═══════════════════════════════════════════════════════════════════════
    print(f"[INFO] Chargement des données...")
    
    train_dataloader = get_dataloader(
        data_dir=config['data']['train_dir'],
        batch_size=config['training']['batch_size'],
        num_workers=config['training']['num_workers'],
        shuffle=True
    )
    
    val_dataloader = get_dataloader(
        data_dir=config['data']['val_dir'],
        batch_size=config['training']['batch_size'],
        num_workers=config['training']['num_workers'],
        shuffle=False
    )
    
    print(f"[INFO] Train: {len(train_dataloader.dataset)} images, {len(train_dataloader)} batches")
    print(f"[INFO] Val:   {len(val_dataloader.dataset)} images, {len(val_dataloader)} batches")

    # ═══════════════════════════════════════════════════════════════════════
    # Modèles
    # ═══════════════════════════════════════════════════════════════════════
    print(f"[INFO] Initialisation des modèles...")
    
    generator = Generator().to(device)
    discriminator = Discriminator().to(device)
    
    initialize_weights(generator)
    initialize_weights(discriminator)
    
    print(f"[INFO] Generator:     {count_parameters(generator):,} paramètres")
    print(f"[INFO] Discriminator: {count_parameters(discriminator):,} paramètres")

    # ═══════════════════════════════════════════════════════════════════════
    # Loss functions et optimizers
    # ═══════════════════════════════════════════════════════════════════════
    criterion_GAN = nn.BCELoss()
    criterion_L1 = nn.L1Loss()
    criterion_perceptual = VGGPerceptualLoss().to(device)
    optimizer_G = torch.optim.Adam(
        generator.parameters(),
        lr=config['training']['lr_G'],
        betas=(config['training']['beta1'], config['training']['beta2'])
    )
    
    optimizer_D = torch.optim.Adam(
        discriminator.parameters(),
        lr=config['training']['lr_D'],
        betas=(config['training']['beta1'], config['training']['beta2'])
    )

    scheduler_G = None
    scheduler_D = None
    if config['training']['scheduler']['enabled']:
        scheduler_G = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer_G,
            mode=config['training']['scheduler']['mode'],
            factor=config['training']['scheduler']['factor'],
            patience=config['training']['scheduler']['patience']
        )
        scheduler_D = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer_D,
            mode=config['training']['scheduler']['mode'],
            factor=config['training']['scheduler']['factor'],
            patience=config['training']['scheduler']['patience']
        )

    # ═══════════════════════════════════════════════════════════════════════
    # Checkpoint manager et logging
    # ═══════════════════════════════════════════════════════════════════════
    checkpoint_manager = CheckpointManager(
        checkpoint_dir=config['checkpointing']['checkpoint_dir'],
        metric_name=config['checkpointing']['metric'],
        mode=config['checkpointing']['mode']
    )

    # TensorBoard
    log_dir = Path(config['logging']['log_dir']) / f"run_{time.strftime('%Y%m%d_%H%M%S')}"
    writer = SummaryWriter(log_dir=str(log_dir))
    # Sauvegarder la config utilisée
    save_config(config, log_dir / 'config.yaml')
    print(f"[INFO] Logs TensorBoard: {log_dir}")

    # Logger de métriques
    metrics_logger = MetricsLogger()

    # Reprendre depuis un checkpoint si spécifié dans la configuration
    start_epoch = 1
    resume_path = config.get('training', {}).get('resume')
    if resume_path:
        print(f"[INFO] Reprise depuis le checkpoint: {resume_path}")
        start_epoch = checkpoint_manager.load_checkpoint(
            resume_path, generator, discriminator, optimizer_G, optimizer_D
        ) + 1

    # ═══════════════════════════════════════════════════════════════════════
    # Boucle d'entraînement
    # ═══════════════════════════════════════════════════════════════════════
    print(f"[INFO] Début de l'entraînement ({config['training']['num_epochs']} epochs)")
    print(f"{'='*70}\n")
    
    training_start_time = time.time()
    
    for epoch in range(start_epoch, config['training']['num_epochs'] + 1):
        epoch_start_time = time.time()
        
        # ───────────────────────────────────────────────────────────────────
        # Phase d'entraînement
        # ───────────────────────────────────────────────────────────────────
        pbar = tqdm(
            total=len(train_dataloader),
            desc=f"Epoch {epoch:>3}/{config['training']['num_epochs']}",
            ncols=100
        )
        
        avg_loss_D, avg_loss_G = train_one_epoch(
            generator, discriminator, train_dataloader,
            optimizer_G, optimizer_D,
            criterion_GAN, criterion_L1,
            config['training']['lambda_l1'],
            device, pbar,config['training']['lambda_vgg'],criterion_perceptual
        )

        pbar.close()

        # ───────────────────────────────────────────────────────────────────
        # Phase de validation
        # ───────────────────────────────────────────────────────────────────
        val_loss_D, val_loss_G, avg_mae, avg_acc = validate(
            generator, discriminator, val_dataloader,
            criterion_GAN, criterion_L1,
            config['training']['lambda_l1'],
            device
        )

        # ───────────────────────────────────────────────────────────────────
        # Mise à jour des schedulers
        # ───────────────────────────────────────────────────────────────────
        if scheduler_G is not None:
            scheduler_G.step(val_loss_G)
            scheduler_D.step(val_loss_D)

        # ───────────────────────────────────────────────────────────────────
        # Logging
        # ───────────────────────────────────────────────────────────────────
        # TensorBoard
        writer.add_scalar('Loss/train_D', avg_loss_D, epoch)
        writer.add_scalar('Loss/train_G', avg_loss_G, epoch)
        writer.add_scalar('Loss/val_D', val_loss_D, epoch)
        writer.add_scalar('Loss/val_G', val_loss_G, epoch)
        writer.add_scalar('LR/generator', optimizer_G.param_groups[0]['lr'], epoch)
        writer.add_scalar('LR/discriminator', optimizer_D.param_groups[0]['lr'], epoch)
        writer.add_scalar('Metrics/MAE', avg_mae, epoch)
        writer.add_scalar('Metrics/Accuracy', avg_acc, epoch)
        
        # Logger de métriques
        metrics_logger.log(
            train_loss_D=avg_loss_D,
            train_loss_G=avg_loss_G,
            val_loss_D=val_loss_D,
            val_loss_G=val_loss_G,
            lr_G=optimizer_G.param_groups[0]['lr'],
            lr_D=optimizer_D.param_groups[0]['lr'],
            mae=avg_mae,
            accuracy=avg_acc
        )
        
        # Sauvegarder des images de validation
        if config['logging']['save_images']:
            save_validation_images(
                generator, val_dataloader, device,
                save_dir=log_dir / 'validation_images',
                epoch=epoch,
                num_images=config['logging']['num_images_to_save']
            )
        
        # ───────────────────────────────────────────────────────────────────
        # Checkpoint
        # ───────────────────────────────────────────────────────────────────
        checkpoint_state = {
            'epoch': epoch,
            'generator': generator.state_dict(),
            'discriminator': discriminator.state_dict(),
            'optimizer_G': optimizer_G.state_dict(),
            'optimizer_D': optimizer_D.state_dict(),
            'config': config,
            'metrics': metrics_logger.get_history()
        }
        
        checkpoint_manager.save_checkpoint(
            checkpoint_state,
            metric_value=val_loss_G,
            epoch=epoch
        )

        # ───────────────────────────────────────────────────────────────────
        # Affichage des résultats
        # ───────────────────────────────────────────────────────────────────
        epoch_time = time.time() - epoch_start_time

        print(f"Loss_D: {avg_loss_D:.4f} → {val_loss_D:.4f}  |  "
            f"Loss_G: {avg_loss_G:.4f} → {val_loss_G:.4f}  |  "
            f"LR: {optimizer_G.param_groups[0]['lr']:.2e}  |  "
            f"Time: {format_time(epoch_time)}")

    # ═══════════════════════════════════════════════════════════════════════
    # Fin de l'entraînement
    # ═══════════════════════════════════════════════════════════════════════
    total_time = time.time() - training_start_time
    
    writer.close()
    
    print(f"\n{'='*70}")
    print(f"Entraînement terminé en {format_time(total_time)}")
    print(f"{'='*70}")
    print(f"Meilleur modèle: {checkpoint_manager.best_checkpoint_path} , model.pt")
    print(f"Meilleur {config['checkpointing']['metric']}: {checkpoint_manager.best_metric:.4f}")
    print(f"Logs TensorBoard: {log_dir}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()

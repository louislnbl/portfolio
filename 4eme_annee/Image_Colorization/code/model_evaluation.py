"""
Outils d'evaluation de modeles entraines pour la colorisation d'images.
"""

import argparse
import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Import des fonctions locales
from model import Generator
from dataset import get_dataloader
from utils import load_config
from metrics import compute_mae, compute_color_accuracy

def evaluate_models(base_dir, val_dir):
    """
    Evalue les meilleurs checkpoints trouves sous base_dir sur un batch de validation.

    Args:
        base_dir (str): Repertoire contenant les experiences (sous-dossiers).
        val_dir (str): Repertoire des donnees de validation.
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    base_path = Path(base_dir)
    
    val_loader = get_dataloader(
        data_dir=val_dir,
        batch_size=5,
        shuffle=False
    )
    
    try:
        gray_batch, real_ab_batch = next(iter(val_loader))
        gray_batch = gray_batch.to(device)
        real_ab_batch = real_ab_batch.to(device)
    except StopIteration:
        print("Erreur : Le DataLoader de validation est vide.")
        return
    
    results = {}
    metrics_summary = {} 
    results['Ground Truth'] = []
    
    experiments = [d for d in base_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    for exp in experiments:
        print(f"Analyse de l'experience : {exp.name}")
        checkpoint_files = list(exp.glob("**/*.pt"))
        if not checkpoint_files:
            continue
        
        best_model_path = checkpoint_files[0]
        
        try:
            gen = Generator().to(device)
            checkpoint = torch.load(best_model_path, map_location=device)
            state_dict = checkpoint['generator'] if isinstance(checkpoint, dict) and 'generator' in checkpoint else checkpoint
            gen.load_state_dict(state_dict)
            gen.eval()
            
            with torch.no_grad():
                fake_ab = gen(gray_batch)
                mae_val = compute_mae(fake_ab, real_ab_batch)
                acc5_val = compute_color_accuracy(fake_ab, real_ab_batch, threshold=5.0)
                acc10_val = compute_color_accuracy(fake_ab, real_ab_batch, threshold=10.0)
                metrics_summary[exp.name] = {
                    "MAE": mae_val, 
                    "Acc5": acc5_val, 
                    "Acc10": acc10_val
                }
            
            generated_images = []
            for i in range(gray_batch.size(0)):
                L = (gray_batch[i].cpu().numpy().transpose(1, 2, 0) + 1.0) * 128.0
                ab = fake_ab[i].cpu().numpy().transpose(1, 2, 0) * 128.0 + 128.0
                lab = np.concatenate([L, ab], axis=-1).astype(np.uint8)
                rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
                generated_images.append(rgb)

                if len(results['Ground Truth']) < gray_batch.size(0):
                    r_ab = real_ab_batch[i].cpu().numpy().transpose(1, 2, 0) * 128.0 + 128.0
                    real_lab = np.concatenate([L, r_ab], axis=-1).astype(np.uint8)
                    results['Ground Truth'].append(cv2.cvtColor(real_lab, cv2.COLOR_LAB2RGB))
            
            results[exp.name] = generated_images

            print(f"[{exp.name}] MAE: {mae_val:.4f} | Acc@5: {acc5_val*100:.2f}% | Acc@10: {acc10_val*100:.2f}%\n")
        except Exception as e:
            print(f"[{exp.name}] Erreur : {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluation des modeles de colorisation entraines")
    parser.add_argument("--base-dir", required=True,
                        help="Repertoire contenant les experiences (un sous-dossier par entrainement)")
    parser.add_argument("--config", default="config.yaml",
                        help="Fichier de configuration donnant le repertoire de validation")
    args = parser.parse_args()

    config = load_config(args.config)
    evaluate_models(base_dir=args.base_dir, val_dir=config["data"]["val_dir"])

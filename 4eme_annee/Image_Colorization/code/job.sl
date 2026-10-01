#!/bin/bash
#═══════════════════════════════════════════════════════════════════════════
# Script SLURM pour l'entraînement du GAN de colorisation sur Arctic (CRIANN)
#═══════════════════════════════════════════════════════════════════════════

#SBATCH -J colorization_gan          # Nom du job
#SBATCH -o output_%J.log             # Fichier de sortie standard
#SBATCH -e error_%J.log              # Fichier de sortie erreur

#──────────────────────────────────────────────────────────────────────────
# Ressources utilisées
#──────────────────────────────────────────────────────────────────────────

# Option 1 - MIG 20GB
#SBATCH -p ar_mig                    # Partition MIG
#SBATCH --gres=gpu:a100_2g.20gb:1    # 1 GPU avec 20GB de VRAM
#SBATCH --cpus-per-gpu=16            # 16 CPUs pour le chargement des données
#SBATCH --mem=32G                    # 32 GB de RAM

# Option 2 - MIG 40GB (si 20GB insuffisant)
# #SBATCH -p ar_mig
# #SBATCH --gres=gpu:a100_3g.40gb:1
# #SBATCH --cpus-per-gpu=16
# #SBATCH --mem=64G

# Option 3 - A100 complète (80GB - à éviter sauf si vraiment nécessaire)
# #SBATCH -p ar_a100
# #SBATCH --gres=gpu:a100:1
# #SBATCH --cpus-per-gpu=32
# #SBATCH --mem=128G

#SBATCH -n 1                         # Nombre de tâches (1 pour un job simple)
#SBATCH --time=08:00:00              # Temps maximum (8h max sur Arctic)

#═══════════════════════════════════════════════════════════════════════════
# Configuration de l'environnement
#═══════════════════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════════════════"
echo "Job SLURM - Colorisation GAN"
echo "═══════════════════════════════════════════════════════════════════════"
echo "Job ID:        $SLURM_JOB_ID"
echo "Node:          $SLURM_NODELIST"
echo "Partition:     $SLURM_JOB_PARTITION"
echo "Start time:    $(date)"
echo "Work dir:      $SLURM_SUBMIT_DIR"
echo "═══════════════════════════════════════════════════════════════════════"

# Aller dans le répertoire de soumission
cd $SLURM_SUBMIT_DIR

# Purger les modules existants
module purge

# Charger le module PyTorch avec CUDA 12.6
# (remplacer par la version disponible sur Arctic - vérifier avec `module avail aidl`)
module load aidl/pytorch/2.6.0-cuda12.6
pip install --user opencv-python-headless

echo ""
echo "Modules chargés:"
module list
echo ""

# Vérifier que CUDA est disponible
echo "CUDA disponible: $(python3 -c 'import torch; print(torch.cuda.is_available())')"
echo "GPU détectée:    $(python3 -c 'import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")')"
echo ""

#═══════════════════════════════════════════════════════════════════════════
# Installation des dépendances supplémentaires (si nécessaire)
#═══════════════════════════════════════════════════════════════════════════

# Vérifier que les dépendances sont installées
python3 -c "import yaml, tensorboard, tqdm, matplotlib" 2>/dev/null || {
    echo "Installation des dépendances manquantes..."
    pip install --user pyyaml tensorboard tqdm matplotlib
}

#═══════════════════════════════════════════════════════════════════════════
# Lancement de l'entraînement
#═══════════════════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════════════════"
echo "Lancement de l'entraînement..."
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Variables configurables
CONFIG_FILE="config.yaml"
EPOCHS=20
LR=0.0002

# Lancer le script d'entraînement
python3 train.py \
    --config "$CONFIG_FILE" \
    --epochs $EPOCHS

# Pour reprendre un entraînement interrompu, décommenter :
# python3 train.py --config "$CONFIG_FILE" --resume checkpoints/best_epochXXX_val_loss_G_X.XXXX.pt

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "Entraînement terminé"
echo "End time: $(date)"
echo "═══════════════════════════════════════════════════════════════════════"

#═══════════════════════════════════════════════════════════════════════════
# Nettoyage
#═══════════════════════════════════════════════════════════════════════════

echo ""
echo "Statistiques du job:"
sacct -j $SLURM_JOB_ID --format=JobID,JobName,Partition,AllocCPUS,State,ExitCode,Elapsed,MaxRSS,MaxVMSize

# Libérer la mémoire cache
sync
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true

#!/bin/bash
# install-ffmpeg.sh - Installation FFmpeg sur VPS Hostinger

echo "🎬 Installation de FFmpeg pour montage vidéo"
echo "=========================================="

# Vérifier si FFmpeg est déjà installé
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg est déjà installé!"
    ffmpeg -version
else
    echo "📦 Installation de FFmpeg..."
    sudo apt update
    sudo apt install -y ffmpeg
    echo "✅ FFmpeg installé avec succès!"
fi

# Créer les dossiers temporaires
echo "📁 Création des dossiers temporaires..."
sudo mkdir -p /tmp/videos
sudo mkdir -p /tmp/montage
sudo chmod 777 /tmp/videos /tmp/montage

echo "✅ Installation terminée!"

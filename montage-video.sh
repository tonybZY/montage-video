#!/bin/bash
# montage-video.sh - Script de montage vidéo

# Variables
TEMP_DIR="/tmp/montage_$(date +%s)"
OUTPUT_DIR="/tmp/videos"

# Fonction de montage
montage_videos() {
    local urls=("$@")
    local video_count=${#urls[@]}
    
    echo "🎬 Montage de $video_count vidéos..."
    
    # Créer dossier temporaire
    mkdir -p "$TEMP_DIR"
    
    # Télécharger les vidéos
    for i in "${!urls[@]}"; do
        echo "📥 Téléchargement vidéo $((i+1))/$video_count..."
        wget -q --show-progress -O "$TEMP_DIR/video_$i.mp4" "${urls[$i]}"
    done
    
    # Créer le fichier de liste pour FFmpeg
    for i in "${!urls[@]}"; do
        echo "file 'video_$i.mp4'" >> "$TEMP_DIR/list.txt"
    done
    
    # Monter avec FFmpeg
    echo "🔧 Montage en cours..."
    OUTPUT_FILE="$OUTPUT_DIR/montage_$(date +%s).mp4"
    ffmpeg -f concat -safe 0 -i "$TEMP_DIR/list.txt" -c copy "$OUTPUT_FILE" -y -loglevel error
    
    # Nettoyer
    echo "🧹 Nettoyage..."
    rm -rf "$TEMP_DIR"
    
    echo "✅ Montage terminé!"
    echo "📍 Fichier: $OUTPUT_FILE"
    
    # Retourner le chemin du fichier
    echo "$OUTPUT_FILE"
}

# Si appelé avec des arguments
if [ $# -gt 0 ]; then
    montage_videos "$@"
fi

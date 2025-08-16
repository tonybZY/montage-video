#!/bin/bash
# test-montage.sh - Tester le montage vidéo

echo "🧪 Test du montage vidéo"
echo "======================="

# URLs de test (remplacez par vos vraies URLs)
VIDEO1="https://example.com/video1.mp4"
VIDEO2="https://example.com/video2.mp4"
VIDEO3="https://example.com/video3.mp4"

# Appeler le script de montage
bash montage-video.sh "$VIDEO1" "$VIDEO2" "$VIDEO3"

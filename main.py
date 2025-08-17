from flask import Flask, request, jsonify, send_file
import requests
import os
import subprocess
import tempfile
import uuid
from datetime import datetime

app = Flask(__name__)

# Dossiers créés par votre script install-ffmpeg.sh
UPLOAD_FOLDER = '/tmp/videos'
OUTPUT_FOLDER = '/tmp/montage'

# Créer les dossiers s'ils n'existent pas (au cas où)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return jsonify({
        "message": "API de montage vidéo",
        "endpoints": {
            "/montage-video": "POST - Assembler plusieurs vidéos en une seule"
        }
    })

@app.route('/montage-video', methods=['POST'])
def montage_video():
    try:
        # DEBUG: Afficher tous les headers reçus
        print("\n=== NOUVELLE REQUÊTE ===")
        print("Headers reçus:")
        for header, value in request.headers:
            print(f"{header}: {value}")
        
        # Vérifier la clé API
        api_key = request.headers.get('X-API-Key')
        print(f"\nAPI Key reçue: '{api_key}'")
        print(f"API Key attendue: 'pk_live_mega_converter_montage_2025'")
        
        if api_key != 'pk_live_mega_converter_montage_2025':
            print(f"ERREUR: Clé API invalide!")
            return jsonify({"error": "Invalid API key", "received": api_key}), 401
        
        print("✓ Authentification réussie")
        
        # Récupérer les données du body
        data = request.get_json()
        print(f"\nDonnées reçues: {data}")
        
        # Vérifier si on a des URLs de vidéos
        if 'video_urls' not in data:
            return jsonify({"error": "video_urls manquant dans le body"}), 400
        
        video_urls = data['video_urls']
        print(f"URLs de vidéos: {video_urls}")
        
        # Liste pour stocker les chemins des vidéos téléchargées
        downloaded_videos = []
        
        # Télécharger chaque vidéo
        for i, url in enumerate(video_urls):
            try:
                print(f"\nTéléchargement de la vidéo {i+1}: {url}")
                # Télécharger la vidéo
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                # Sauvegarder temporairement
                temp_filename = f"{UPLOAD_FOLDER}/video_{i}_{uuid.uuid4()}.mp4"
                with open(temp_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded_videos.append(temp_filename)
                print(f"✓ Vidéo {i+1} téléchargée: {temp_filename}")
                
            except Exception as e:
                print(f"✗ Erreur lors du téléchargement de la vidéo {i+1}: {str(e)}")
                # Nettoyer les vidéos déjà téléchargées
                for video in downloaded_videos:
                    if os.path.exists(video):
                        os.remove(video)
                return jsonify({"error": f"Erreur téléchargement vidéo {i+1}: {str(e)}"}), 500
        
        # Créer un fichier texte avec la liste des vidéos pour FFmpeg
        list_filename = f"{UPLOAD_FOLDER}/list_{uuid.uuid4()}.txt"
        with open(list_filename, 'w') as f:
            for video in downloaded_videos:
                f.write(f"file '{os.path.abspath(video)}'\n")
        print(f"\nFichier de liste créé: {list_filename}")
        
        # Nom du fichier de sortie
        output_filename = f"{OUTPUT_FOLDER}/montage_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()}.mp4"
        
        # Commande FFmpeg pour assembler les vidéos
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_filename,
            '-c', 'copy',  # Copie sans réencodage pour plus de rapidité
            output_filename,
            '-y'  # Écraser si le fichier existe
        ]
        
        print(f"\nExécution de FFmpeg...")
        print(f"Commande: {' '.join(cmd)}")
        
        # Exécuter FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Erreur FFmpeg: {result.stderr}")
            # Nettoyer les fichiers temporaires
            cleanup_temp_files(downloaded_videos, list_filename)
            return jsonify({"error": "Erreur lors du montage vidéo", "details": result.stderr}), 500
        
        print(f"✓ Montage réussi: {output_filename}")
        
        # Nettoyer les fichiers temporaires
        cleanup_temp_files(downloaded_videos, list_filename)
        
        # Créer l'URL de la vidéo montée
        video_url = f"http://31.97.53.91:5000/download/{os.path.basename(output_filename)}"
        
        response_data = {
            "success": True,
            "message": "Vidéo montée avec succès",
            "montage_url": video_url,
            "duration": len(video_urls) * 8,  # Si chaque vidéo fait 8 secondes
            "videos_count": len(video_urls)
        }
        
        print(f"\nRéponse envoyée: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"\n✗ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_video(filename):
    """Route pour télécharger la vidéo montée"""
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        print(f"Téléchargement de: {file_path}")
        return send_file(file_path, mimetype='video/mp4')
    return jsonify({"error": "Fichier non trouvé"}), 404

def cleanup_temp_files(video_files, list_file):
    """Nettoyer les fichiers temporaires"""
    print("\nNettoyage des fichiers temporaires...")
    for video in video_files:
        if os.path.exists(video):
            os.remove(video)
            print(f"✓ Supprimé: {video}")
    if os.path.exists(list_file):
        os.remove(list_file)
        print(f"✓ Supprimé: {list_file}")

if __name__ == '__main__':
    print("=== API de montage vidéo démarrée ===")
    print(f"Dossier vidéos: {UPLOAD_FOLDER}")
    print(f"Dossier montages: {OUTPUT_FOLDER}")
    print("=====================================\n")
    app.run(host='0.0.0.0', port=5000, debug=True)

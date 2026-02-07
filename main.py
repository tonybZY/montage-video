from flask import Flask, request, jsonify, send_file
import requests
import os
import subprocess
import tempfile
import uuid
from datetime import datetime

app = Flask(__name__)

# Dossiers temporaires
UPLOAD_FOLDER = '/tmp/videos'
OUTPUT_FOLDER = '/tmp/montage'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# URL de base Railway (variable d'environnement ou fallback)
RAILWAY_URL = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-60365.up.railway.app')

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
        print("\n=== NOUVELLE REQUÊTE ===")
        print("Headers reçus:")
        for header, value in request.headers:
            print(f"{header}: {value}")
        
        # Vérifier la clé API
        api_key = request.headers.get('X-API-Key')
        print(f"\nAPI Key reçue: '{api_key}'")
        
        if api_key != 'pk_live_mega_converter_montage_2025':
            print(f"ERREUR: Clé API invalide!")
            return jsonify({"error": "Invalid API key", "received": api_key}), 401
        
        print("✓ Authentification réussie")
        
        # Récupérer les données du body
        data = request.get_json()
        print(f"\nDonnées reçues: {data}")
        
        if not data or 'video_urls' not in data:
            return jsonify({"error": "video_urls manquant dans le body"}), 400
        
        video_urls = data['video_urls']
        print(f"URLs de vidéos: {video_urls}")
        
        if not video_urls or len(video_urls) == 0:
            return jsonify({"error": "La liste video_urls est vide"}), 400
        
        # Télécharger chaque vidéo
        downloaded_videos = []
        
        for i, url in enumerate(video_urls):
            try:
                print(f"\nTéléchargement de la vidéo {i+1}: {url}")
                response = requests.get(url, stream=True, timeout=120)
                response.raise_for_status()
                
                temp_filename = f"{UPLOAD_FOLDER}/video_{i}_{uuid.uuid4()}.mp4"
                with open(temp_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Vérifier que le fichier n'est pas vide
                file_size = os.path.getsize(temp_filename)
                print(f"✓ Vidéo {i+1} téléchargée: {temp_filename} ({file_size} bytes)")
                
                if file_size == 0:
                    raise Exception(f"Le fichier téléchargé est vide pour l'URL: {url}")
                
                downloaded_videos.append(temp_filename)
                
            except Exception as e:
                print(f"✗ Erreur téléchargement vidéo {i+1}: {str(e)}")
                for video in downloaded_videos:
                    if os.path.exists(video):
                        os.remove(video)
                return jsonify({"error": f"Erreur téléchargement vidéo {i+1}: {str(e)}"}), 500
        
        # Vérifier les codecs de chaque vidéo
        print("\n--- Analyse des vidéos ---")
        video_infos = []
        for video in downloaded_videos:
            probe_cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=codec_name,width,height',
                '-of', 'csv=p=0',
                video
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            info = probe_result.stdout.strip()
            video_infos.append(info)
            print(f"  {os.path.basename(video)}: {info}")
        
        # Vérifier si tous les codecs/résolutions sont identiques
        all_same = len(set(video_infos)) == 1
        print(f"  Tous identiques: {all_same}")
        
        # Créer le fichier liste pour FFmpeg
        list_filename = f"{UPLOAD_FOLDER}/list_{uuid.uuid4()}.txt"
        with open(list_filename, 'w') as f:
            for video in downloaded_videos:
                f.write(f"file '{os.path.abspath(video)}'\n")
        print(f"\nFichier de liste créé: {list_filename}")
        
        # Nom du fichier de sortie
        output_filename = f"{OUTPUT_FOLDER}/montage_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()}.mp4"
        
        if all_same:
            # Copie directe sans réencodage (rapide)
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_filename,
                '-c', 'copy',
                output_filename
            ]
        else:
            # Réencodage nécessaire (vidéos de formats différents)
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_filename,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                output_filename
            ]
        
        print(f"\nExécution de FFmpeg...")
        print(f"Commande: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            print(f"✗ Erreur FFmpeg: {result.stderr}")
            cleanup_temp_files(downloaded_videos, list_filename)
            return jsonify({"error": "Erreur lors du montage vidéo", "details": result.stderr}), 500
        
        # Vérifier que le fichier de sortie existe et n'est pas vide
        if not os.path.exists(output_filename) or os.path.getsize(output_filename) == 0:
            cleanup_temp_files(downloaded_videos, list_filename)
            return jsonify({"error": "Le fichier de sortie est vide ou n'existe pas"}), 500
        
        output_size = os.path.getsize(output_filename)
        print(f"✓ Montage réussi: {output_filename} ({output_size} bytes)")
        
        # Nettoyer les fichiers temporaires (pas le fichier de sortie!)
        cleanup_temp_files(downloaded_videos, list_filename)
        
        # Vérifier le paramètre return_file pour renvoyer directement le fichier
        return_file = data.get('return_file', False)
        
        if return_file:
            # Renvoyer directement le fichier vidéo dans la réponse
            print("→ Envoi direct du fichier vidéo")
            return send_file(
                output_filename,
                mimetype='video/mp4',
                as_attachment=True,
                download_name=f"montage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )
        else:
            # Renvoyer un JSON avec l'URL de téléchargement (URL Railway correcte)
            download_url = f"https://{RAILWAY_URL}/download/{os.path.basename(output_filename)}"
            
            response_data = {
                "success": True,
                "message": "Vidéo montée avec succès",
                "download_url": download_url,
                "file_size": output_size,
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
        return send_file(file_path, mimetype='video/mp4', as_attachment=True, download_name=filename)
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
    port = int(os.environ.get('PORT', 5000))
    print("=== API de montage vidéo démarrée ===")
    print(f"Port: {port}")
    print(f"Railway URL: {RAILWAY_URL}")
    print(f"Dossier vidéos: {UPLOAD_FOLDER}")
    print(f"Dossier montages: {OUTPUT_FOLDER}")
    print("=====================================\n")
    app.run(host='0.0.0.0', port=port, debug=False)

from flask import Flask, request, jsonify, send_file
import requests
import os
import subprocess
import uuid
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp/videos'
OUTPUT_FOLDER = '/tmp/montage'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

RAILWAY_URL = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
API_KEY = os.environ.get('API_KEY', 'pk_live_montage_2025')


@app.route('/')
def home():
    return jsonify({
        "message": "API de montage vidéo",
        "version": "2.0",
        "endpoints": {
            "POST /montage-video": "Assembler plusieurs vidéos en une seule",
            "GET /download/<filename>": "Télécharger une vidéo montée"
        }
    })


@app.route('/montage-video', methods=['POST'])
def montage_video():
    try:
        # --- Auth ---
        api_key = request.headers.get('X-API-Key', '')
        if api_key != API_KEY:
            return jsonify({"error": "Clé API invalide"}), 401

        # --- Body ---
        data = request.get_json(silent=True)
        if not data or 'video_urls' not in data:
            return jsonify({"error": "Body JSON requis avec 'video_urls': ['url1', 'url2', ...]"}), 400

        video_urls = data['video_urls']
        if not isinstance(video_urls, list) or len(video_urls) < 2:
            return jsonify({"error": "Il faut au moins 2 URLs de vidéos"}), 400

        print(f"\n=== MONTAGE: {len(video_urls)} vidéos ===")

        # --- Télécharger les vidéos ---
        downloaded = []
        try:
            for i, url in enumerate(video_urls):
                print(f"Téléchargement {i+1}/{len(video_urls)}: {url[:80]}...")
                resp = requests.get(url, stream=True, timeout=120)
                resp.raise_for_status()

                path = f"{UPLOAD_FOLDER}/vid_{i}_{uuid.uuid4().hex[:8]}.mp4"
                with open(path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)

                size = os.path.getsize(path)
                if size == 0:
                    raise Exception(f"Fichier vide pour URL {i+1}")
                print(f"  ✓ {size} bytes")
                downloaded.append(path)

        except Exception as e:
            cleanup(downloaded)
            return jsonify({"error": f"Erreur téléchargement: {str(e)}"}), 500

        # --- Créer la liste FFmpeg ---
        list_file = f"{UPLOAD_FOLDER}/list_{uuid.uuid4().hex[:8]}.txt"
        with open(list_file, 'w') as f:
            for path in downloaded:
                f.write(f"file '{os.path.abspath(path)}'\n")

        # --- Montage FFmpeg ---
        output_name = f"montage_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.mp4"
        output_path = f"{OUTPUT_FOLDER}/{output_name}"

        # D'abord essayer sans réencodage (rapide)
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-movflags', '+faststart',
            output_path
        ]
        print(f"FFmpeg (copy)...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        # Si ça échoue, réencoder
        if result.returncode != 0:
            print(f"Copy échoué, réencodage...")
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0',
                '-i', list_file,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                '-c:a', 'aac', '-b:a', '128k',
                '-movflags', '+faststart',
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        # Nettoyer les fichiers temporaires
        cleanup(downloaded, list_file)

        if result.returncode != 0:
            return jsonify({"error": "Erreur FFmpeg", "details": result.stderr[-500:]}), 500

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return jsonify({"error": "Fichier de sortie vide"}), 500

        output_size = os.path.getsize(output_path)
        print(f"✓ Montage OK: {output_name} ({output_size} bytes)")

        # --- Réponse ---
        return_file = data.get('return_file', False)

        if return_file:
            return send_file(
                output_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name=output_name
            )
        else:
            base = RAILWAY_URL or request.host
            scheme = 'https' if RAILWAY_URL else request.scheme
            download_url = f"{scheme}://{base}/download/{output_name}"

            return jsonify({
                "success": True,
                "message": "Vidéo montée avec succès",
                "download_url": download_url,
                "file_size": output_size,
                "videos_count": len(video_urls)
            })

    except Exception as e:
        print(f"Erreur: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/download/<filename>')
def download_video(filename):
    # Sécurité: empêcher path traversal
    filename = os.path.basename(filename)
    path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, mimetype='video/mp4', as_attachment=True, download_name=filename)
    return jsonify({"error": "Fichier non trouvé"}), 404


def cleanup(files, list_file=None):
    for f in files:
        if os.path.exists(f):
            os.remove(f)
    if list_file and os.path.exists(list_file):
        os.remove(list_file)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"=== API Montage Vidéo v2.0 | Port {port} ===")
    app.run(host='0.0.0.0', port=port)

# main.py - Montage Video API
from flask import Flask, request, jsonify
import requests
import os
from typing import List, Dict
import time

app = Flask(__name__)

# Configuration
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'https://n8n.srv840088.hstgr.cloud/workflow/...')
API_KEY = os.getenv('API_KEY', 'your-api-key-here')

@app.route('/')
def home():
    return jsonify({
        "service": "Montage Video API",
        "status": "active",
        "endpoints": {
            "/video-urls": "POST - Additionner les URLs vidéo pour montage",
            "/notify-n8n": "POST - Envoyer une notification à n8n",
            "/montage-video": "POST - Traiter et monter les vidéos via n8n"
        }
    })

@app.route('/video-urls', methods=['POST'])
def handle_video_urls():
    """Endpoint pour recevoir et additionner les URLs vidéo pour montage"""
    try:
        # Vérifier la clé API
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.json
        video_urls = data.get('video_urls', [])
        
        if isinstance(video_urls, str):
            video_urls = [video_urls]
        
        # Préparer la liste des vidéos pour le montage
        montage_sequence = []
        
        # Additionner chaque URL vidéo dans l'ordre
        for idx, url in enumerate(video_urls):
            video_info = {
                "position": idx + 1,
                "url": url,
                "download_url": url,
                "timestamp": time.time(),
                "status": "ready_for_montage"
            }
            montage_sequence.append(video_info)
            
            # Petit délai entre chaque vidéo pour éviter la surcharge
            if idx < len(video_urls) - 1:
                time.sleep(0.2)
        
        return jsonify({
            "success": True,
            "total_videos": len(montage_sequence),
            "montage_sequence": montage_sequence,
            "message": f"{len(montage_sequence)} vidéos prêtes pour le montage"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/notify-n8n', methods=['POST'])
def notify_n8n():
    """Envoyer une notification à n8n"""
    try:
        # Vérifier la clé API
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.json
        
        # Préparer les données pour n8n
        n8n_payload = {
            "timestamp": time.time(),
            "source": "montage-video-api",
            "data": data
        }
        
        # Envoyer à n8n
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
        
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=n8n_payload,
            headers=headers,
            timeout=30
        )
        
        return jsonify({
            "success": True,
            "n8n_response": response.status_code,
            "message": "Notification sent to n8n"
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to notify n8n: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/montage-video', methods=['POST'])
def montage_video():
    """Traiter les URLs vidéo et déclencher le montage via n8n"""
    try:
        # Vérifier la clé API
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.json
        video_urls = data.get('video_urls', [])
        title = data.get('title', 'Montage Video')
        output_format = data.get('output_format', 'mp4')
        
        if isinstance(video_urls, str):
            video_urls = [video_urls]
        
        # Vérifier qu'il y a au moins 2 vidéos pour un montage
        if len(video_urls) < 2:
            return jsonify({
                "error": "Au moins 2 vidéos sont nécessaires pour un montage"
            }), 400
        
        montage_sequence = []
        
        # Préparer la séquence de montage
        for idx, url in enumerate(video_urls):
            video_info = {
                "position": idx + 1,
                "url": url,
                "download_url": url,
                "timestamp": time.time()
            }
            montage_sequence.append(video_info)
        
        # Préparer le payload pour n8n avec toutes les vidéos
        n8n_montage_payload = {
            "event": "montage_video_request",
            "title": title,
            "output_format": output_format,
            "total_videos": len(montage_sequence),
            "video_sequence": montage_sequence,
            "timestamp": time.time(),
            "instructions": "Additionner les vidéos dans l'ordre de position"
        }
        
        # Envoyer la requête de montage à n8n
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
        
        try:
            response = requests.post(
                N8N_WEBHOOK_URL,
                json=n8n_montage_payload,
                headers=headers,
                timeout=30
            )
            
            montage_triggered = response.status_code == 200
            
            return jsonify({
                "success": True,
                "message": f"Montage de {len(montage_sequence)} vidéos déclenché",
                "montage_triggered": montage_triggered,
                "title": title,
                "output_format": output_format,
                "video_sequence": montage_sequence,
                "n8n_response_status": response.status_code
            })
            
        except requests.exceptions.RequestException as e:
            return jsonify({
                "error": f"Erreur lors de l'envoi à n8n: {str(e)}",
                "video_sequence": montage_sequence
            }), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

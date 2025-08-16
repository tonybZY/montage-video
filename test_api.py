# test_api.py - Script pour tester l'API Montage Video
import requests
import json
import time

# Configuration
API_URL = "http://localhost:5000"  # Changer pour votre URL Railway en production
API_KEY = "your-api-key-here"

def test_home():
    """Test de l'endpoint home"""
    print("🔍 Test de l'endpoint /")
    response = requests.get(f"{API_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_video_urls():
    """Test de l'addition des URLs vidéo"""
    print("🎬 Test de /video-urls")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "video_urls": [
            "https://example.com/intro.mp4",
            "https://example.com/content.mp4",
            "https://example.com/outro.mp4"
        ]
    }
    
    response = requests.post(
        f"{API_URL}/video-urls",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_notify_n8n():
    """Test de notification n8n"""
    print("📨 Test de /notify-n8n")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "message": "Test notification from Montage Video API",
        "timestamp": time.time(),
        "data": {
            "test": True,
            "source": "test_montage_video"
        }
    }
    
    response = requests.post(
        f"{API_URL}/notify-n8n",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_montage_video():
    """Test du montage vidéo complet"""
    print("🎥 Test de /montage-video")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "video_urls": [
            "https://pdf-converter-server-production.up.railway.app/download/video1.mp4",
            "https://pdf-converter-server-production.up.railway.app/download/video2.mp4",
            "https://pdf-converter-server-production.up.railway.app/download/video3.mp4"
        ],
        "title": "Test Montage Video",
        "output_format": "mp4"
    }
    
    response = requests.post(
        f"{API_URL}/montage-video",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_montage_minimum_videos():
    """Test avec moins de 2 vidéos (devrait échouer)"""
    print("⚠️ Test avec une seule vidéo (devrait échouer)")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "video_urls": [
            "https://example.com/single-video.mp4"
        ],
        "title": "Test Single Video"
    }
    
    response = requests.post(
        f"{API_URL}/montage-video",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_unauthorized():
    """Test avec une mauvaise clé API"""
    print("🚫 Test d'accès non autorisé")
    
    headers = {
        "X-API-Key": "wrong-key",
        "Content-Type": "application/json"
    }
    
    data = {"video_urls": ["https://example.com/test.mp4"]}
    
    response = requests.post(
        f"{API_URL}/video-urls",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

if __name__ == "__main__":
    print("🚀 Démarrage des tests de l'API Montage Video")
    print("=" * 50)
    
    try:
        # Test 1: Home
        test_home()
        time.sleep(1)
        
        # Test 2: Unauthorized
        test_unauthorized()
        time.sleep(1)
        
        # Test 3: Video URLs
        test_video_urls()
        time.sleep(1)
        
        # Test 4: Minimum videos check
        test_montage_minimum_videos()
        time.sleep(1)
        
        # Test 5: Notify n8n (commenté par défaut pour éviter de spammer n8n)
        # test_notify_n8n()
        # time.sleep(1)
        
        # Test 6: Montage Video (commenté par défaut)
        # test_montage_video()
        
        print("\n✅ Tests terminés!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter à l'API.")
        print("Assurez-vous que l'API est en cours d'exécution sur", API_URL)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

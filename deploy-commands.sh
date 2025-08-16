#!/bin/bash

# Script de déploiement pour Montage Video API

echo "🎬 Déploiement de Montage Video API"
echo "===================================="

# 1. Initialiser Git
echo "📁 Initialisation du repository Git..."
git init

# 2. Ajouter tous les fichiers
echo "➕ Ajout des fichiers..."
git add .

# 3. Premier commit
echo "💾 Création du premier commit..."
git commit -m "Initial commit - Montage Video API"

# 4. Renommer la branche principale
echo "🌿 Configuration de la branche main..."
git branch -M main

# 5. Configurer le remote GitHub
echo "🔗 Configuration du remote GitHub..."
echo "⚠️  N'oubliez pas de créer le repository sur GitHub d'abord!"
echo "Entrez votre nom d'utilisateur GitHub:"
read github_username

git remote add origin https://github.com/$github_username/montage-video.git

# 6. Push vers GitHub
echo "🚀 Push vers GitHub..."
git push -u origin main

echo ""
echo "✅ Repository GitHub créé!"
echo ""
echo "📦 Prochaines étapes:"
echo "1. Allez sur https://railway.app"
echo "2. Créez un nouveau projet"
echo "3. Connectez votre repository GitHub"
echo "4. Ajoutez ces variables d'environnement:"
echo "   - N8N_WEBHOOK_URL: Votre URL webhook n8n"
echo "   - API_KEY: Votre clé API secrète"
echo ""
echo "🎥 Votre API Montage Video sera prête!"

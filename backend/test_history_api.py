"""
Test de l'API d'historique des emails
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_history():
    print("=" * 60)
    print("TEST DE L'API D'HISTORIQUE")
    print("=" * 60)
    
    # 1. Login
    print("\n1️⃣ Connexion...")
    login_data = {
        "username": "awone@h-tsoft.com",
        "password": "Passer123"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"✅ Connexion réussie")
            print(f"   Token: {token[:50]}...")
        else:
            print(f"❌ Échec de connexion: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # 2. Récupérer l'historique
    print("\n2️⃣ Récupération de l'historique...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/email-history-periods?limit=5", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Historique récupéré: {len(history)} périodes")
            print("\n📅 Périodes:")
            for period in history:
                print(f"\n  📌 {period['period']}")
                print(f"     Dernière activité: {period['date_time']}")
                print(f"     Bulletins: {period['bulletins_count']}")
                print(f"     Statut: {period['status_summary']}")
        else:
            print(f"❌ Échec: {response.status_code}")
            print(f"   Réponse: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 3. Récupérer les statistiques
    print("\n3️⃣ Récupération des statistiques...")
    try:
        response = requests.get(f"{BASE_URL}/email-stats", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistiques récupérées:")
            print(f"   Total: {stats.get('total', 0)}")
            print(f"   Envoyés: {stats.get('sent', 0)}")
            print(f"   Échoués: {stats.get('failed', 0)}")
            print(f"   En attente: {stats.get('pending', 0)}")
        else:
            print(f"❌ Échec: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_history()


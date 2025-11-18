"""
Script de test pour les nouveaux endpoints du dashboard Super Admin
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_dashboard_endpoints():
    print("=" * 60)
    print("TEST DES ENDPOINTS DU DASHBOARD SUPER ADMIN")
    print("=" * 60)
    
    # 1. Connexion en tant que super admin
    print("\n1️⃣ Connexion en tant que super admin...")
    login_data = {
        "username": "admin@admin.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Connexion réussie")
            print(f"   Token: {token[:20]}...")
        else:
            print(f"❌ Échec de connexion: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test de l'endpoint users-stats
    print("\n2️⃣ Test de l'endpoint /users-stats...")
    try:
        response = requests.get(f"{BASE_URL}/users-stats", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistiques utilisateurs récupérées:")
            print(f"   Total utilisateurs: {stats.get('total_users', 0)}")
            print(f"   Employés actifs: {stats.get('active_employees', 0)}")
        else:
            print(f"❌ Échec: {response.status_code}")
            print(f"   Réponse: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 3. Test de l'endpoint email-recent-activity-detailed
    print("\n3️⃣ Test de l'endpoint /email-recent-activity-detailed...")
    try:
        response = requests.get(f"{BASE_URL}/email-recent-activity-detailed?limit=5", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            activities = response.json()
            print(f"✅ Activités récentes récupérées: {len(activities)} activités")
            
            if activities:
                print("\n📋 Détails des activités:")
                for i, activity in enumerate(activities, 1):
                    print(f"\n   {i}. {activity.get('employee', 'N/A')}")
                    print(f"      Email: {activity.get('email', 'N/A')}")
                    print(f"      Statut: {activity.get('status', 'N/A')}")
                    print(f"      Date: {activity.get('date', 'N/A')}")
                    print(f"      Bulletin: {activity.get('bulletinMonth', 'N/A')}")
            else:
                print("   ℹ️ Aucune activité récente trouvée")
        else:
            print(f"❌ Échec: {response.status_code}")
            print(f"   Réponse: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 4. Test de l'endpoint email-stats (existant)
    print("\n4️⃣ Test de l'endpoint /email-stats (existant)...")
    try:
        response = requests.get(f"{BASE_URL}/email-stats", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistiques emails récupérées:")
            print(f"   Total: {stats.get('total', 0)}")
            print(f"   Envoyés: {stats.get('sent', 0)}")
            print(f"   Échoués: {stats.get('failed', 0)}")
            print(f"   En attente: {stats.get('pending', 0)}")
        else:
            print(f"❌ Échec: {response.status_code}")
            print(f"   Réponse: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("✅ TESTS TERMINÉS")
    print("=" * 60)

if __name__ == "__main__":
    test_dashboard_endpoints()


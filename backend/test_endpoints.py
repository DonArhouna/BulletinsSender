"""
Script de test pour vérifier les endpoints du dashboard
"""
import requests
import json

# URL de base
BASE_URL = "http://localhost:8000/api/v1"

def test_endpoints():
    """Test les endpoints principaux"""
    
    print("=" * 60)
    print("TEST DES ENDPOINTS")
    print("=" * 60)
    
    # Vous devrez remplacer ce token par un vrai token valide
    # Pour obtenir un token, connectez-vous d'abord via l'interface
    token = input("\nEntrez votre token d'authentification (ou appuyez sur Entrée pour un test sans auth): ").strip()
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # Test 1: Endpoint email-stats
    print("\n" + "-" * 60)
    print("1. Test de /email-stats")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/email-stats", headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Succès!")
            print(f"Données: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Endpoint users-stats (superadmin)
    print("\n" + "-" * 60)
    print("2. Test de /users-stats (endpoint superadmin)")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/users-stats", headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Succès!")
            print(f"Données: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Endpoint user-stats (client)
    print("\n" + "-" * 60)
    print("3. Test de /user-stats (endpoint client)")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/user-stats", headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Succès!")
            print(f"Données: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Endpoint email-history-periods
    print("\n" + "-" * 60)
    print("4. Test de /email-history-periods")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/email-history-periods?limit=3", headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Succès!")
            print(f"Nombre de périodes: {len(data)}")
            if data:
                print(f"Données: {json.dumps(data, indent=2)}")
            else:
                print("ℹ️ Aucune donnée d'historique (normal si aucun email n'a été envoyé)")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("FIN DES TESTS")
    print("=" * 60)
    print("\nNOTES:")
    print("- Si vous voyez des erreurs 401, vous devez fournir un token valide")
    print("- Si vous voyez des erreurs 403, votre compte n'a pas les permissions")
    print("- Les endpoints *-stats nécessitent une authentification")
    print()

if __name__ == "__main__":
    test_endpoints()

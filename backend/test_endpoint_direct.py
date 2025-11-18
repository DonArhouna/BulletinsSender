"""
Test direct de l'endpoint avec requests
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login
print("1. Login...")
login_response = requests.post(f"{BASE_URL}/auth/login", data={
    "username": "admin@admin.com",
    "password": "admin123"
})

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print(f"✅ Token: {token[:20]}...")

headers = {"Authorization": f"Bearer {token}"}

# 2. Test email-recent-activity-detailed
print("\n2. Test /email-recent-activity-detailed...")
try:
    response = requests.get(f"{BASE_URL}/email-recent-activity-detailed?limit=5", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Success! {len(data)} activities")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()


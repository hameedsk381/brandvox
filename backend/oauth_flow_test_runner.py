import httpx
import asyncio

API_URL = "http://localhost:8000"

async def test_flow():
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("1. Logging in...")
        resp = await client.post(f"{API_URL}/api/auth/login", json={"email": "agency@stellar.digital", "password": "demo1234"})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get ME to find agency_id
        print("2. Getting User Info...")
        resp = await client.get(f"{API_URL}/api/auth/me", headers=headers)
        user = resp.json()
        agency_id = user["agency_id"]
        
        # We need a client_id for the auth URL. Let's get the first client for this agency.
        resp = await client.get(f"{API_URL}/api/clients", headers=headers)
        clients = resp.json()
        client_id = clients[0]["id"]
        print(f"   Found Agency: {agency_id}, Client: {client_id}")
        
        # 3. Try to get auth URL BEFORE setting credentials
        print("3. Testing /auth-url without credentials...")
        resp = await client.get(f"{API_URL}/api/integrations/google/auth-url?client_id={client_id}", headers=headers)
        print(f"   Expected 400: {resp.status_code} - {resp.json()}")
        
        # 4. Set credentials
        print("4. Setting Google Credentials via UI API...")
        resp = await client.put(
            f"{API_URL}/api/agencies/{agency_id}/google-credentials",
            json={"client_id": "test-client-id", "client_secret": "test-client-secret"},
            headers=headers
        )
        print(f"   Response: {resp.status_code} - {resp.json()}")
        
        # 5. Try to get auth URL AFTER setting credentials
        print("5. Testing /auth-url WITH credentials...")
        resp = await client.get(f"{API_URL}/api/integrations/google/auth-url?client_id={client_id}", headers=headers)
        print(f"   Expected 200: {resp.status_code} - {resp.json()}")
        
        # 6. Test Callback
        print("6. Testing /callback...")
        resp = await client.post(
            f"{API_URL}/api/integrations/google/callback?code=auth_code_123&state={client_id}",
            headers=headers
        )
        print(f"   Response: {resp.status_code} - {resp.json()}")
        
        # 7. Get Locations
        print("7. Testing /locations...")
        resp = await client.get(f"{API_URL}/api/integrations/google/locations?client_id={client_id}", headers=headers)
        print(f"   Response: {resp.status_code} - {resp.json()}")

if __name__ == "__main__":
    asyncio.run(test_flow())

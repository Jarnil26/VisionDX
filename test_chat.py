import httpx

def test_chat():
    r1 = httpx.post("http://localhost:8002/users/register", json={"email": "testchat99@example.com", "password": "password123", "full_name": "Test User", "role": "patient"})
    if r1.status_code >= 400:
        r1 = httpx.post("http://localhost:8002/users/login", json={"email": "testchat99@example.com", "password": "password123"})
    
    if r1.status_code != 200 and r1.status_code != 201:
        print("Login failed:", r1.text)
        return
        
    token = r1.json()["access_token"]
    print("Logged in. Testing chat...")
    
    r2 = httpx.post(
        "http://localhost:8002/chat", 
        json={"message": "tengo mucho dolor de pecho"}, 
        headers={"Authorization": f"Bearer {token}"}
    )
    print("Status:", r2.status_code)
    print("Response:", r2.text)

if __name__ == "__main__":
    test_chat()

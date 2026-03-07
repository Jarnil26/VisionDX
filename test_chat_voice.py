import httpx
import os

def test_chat_voice():
    # Login again to get token
    r1 = httpx.post("http://localhost:8002/users/login", json={"email": "testchat99@example.com", "password": "password123"})
    if r1.status_code != 200:
        print("Login failed:", r1.text)
        return
        
    token = r1.json()["access_token"]
    print("Logged in. Testing voice chat...")
    
    # Create a dummy wav file larger than 100 bytes
    dummy_audio = b"RIFF" + b"\x00" * 200
    with open("dummy.wav", "wb") as f:
        f.write(dummy_audio)
    
    with open("dummy.wav", "rb") as f:
        files = {"audio": ("dummy.wav", f, "audio/wav")}
        data = {"lang": "es"}
        r2 = httpx.post(
            "http://localhost:8002/chat/voice", 
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
    print("Status:", r2.status_code)
    print("Response:", r2.text)

if __name__ == "__main__":
    test_chat_voice()

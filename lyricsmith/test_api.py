#!/usr/bin/env python3
"""
Test the FastAPI backend
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing LyricSmith API")
    print("=" * 70)
    
    # 1. Health check
    print("\n1. Health Check...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print(f"   Status: {response.json()}")
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return
    
    # 2. Configure LLM
    print("\n2. Configuring LLM (Ollama with Qwen2.5:7b)...")
    config = {
        "backend": "ollama",
        "model": "qwen2.5:7b"
    }
    response = requests.post(f"{BASE_URL}/config", json=config)
    if response.status_code == 200:
        print(f"   Result: {response.json()}")
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return
    
    # 3. Create a song
    print("\n3. Creating song...")
    song_data = {"title": "API Test Song"}
    response = requests.post(f"{BASE_URL}/songs", json=song_data)
    if response.status_code != 200:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return
    song = response.json()
    song_id = song["song_id"]
    print(f"   Song ID: {song_id}")
    print(f"   Title: {song['title']}")
    
    # 4. Generate lyrics
    print("\n4. Generating lyrics (this takes 2-4 minutes)...")
    generate_request = {
        "song_id": song_id,
        "section_name": "verse1",
        "lines": [
    {"meaning": "walking down the empty street at night", "syllables": 10, "rhyme_label": "A"},
    {"meaning": "the city lights are shining bright", "syllables": 8, "rhyme_label": "A"},
    {"meaning": "my heart is feeling kind of blue", "syllables": 8, "rhyme_label": "B"},
    {"meaning": "thinking only about you", "syllables": 7, "rhyme_label": "B"},
],
"rhyme_scheme": "AABB",

        "strictness": "sung"
    }
    
    response = requests.post(f"{BASE_URL}/generate", json=generate_request)
    
    # Check if response is valid
    if response.status_code != 200:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    try:
        job = response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"   ❌ Invalid JSON response")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    job_id = job["job_id"]
    print(f"   Job ID: {job_id}")
    print(f"   Status: {job['status']}")
    
    # 5. Poll for completion
    print("\n5. Waiting for completion...")
    while True:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        job = response.json()
        status = job["status"]
        print(f"   Status: {status}")
        
        if status == "completed":
            print("\n   ✅ Generation completed!")
            print("\n   Generated Lines:")
            for i, line in enumerate(job["lines"], 1):
                result = job["results"][i-1]
                icon = "✅" if result["status"] == "PASS" else "❌"
                print(f"      {icon} Line {i}: {line or '(failed)'}")
                print(f"         Attempts: {result['attempts']}")
            break
        
        elif status == "failed":
            print(f"\n   ❌ Generation failed: {job.get('error')}")
            break
        
        time.sleep(5)  # Poll every 5 seconds
    
    # 6. Get song
    print("\n6. Retrieving complete song...")
    response = requests.get(f"{BASE_URL}/songs/{song_id}")
    song = response.json()
    print(f"   Title: {song['title']}")
    print(f"   Sections: {list(song['sections'].keys())}")
    
    if "verse1" in song["sections"]:
        print("\n   Verse 1:")
        for i, line in enumerate(song["sections"]["verse1"]["lines"], 1):
            print(f"      {i}. {line}")
    
    print("\n" + "=" * 70)
    print("✅ API test completed!")
    print("\n📝 API is ready for frontend integration")
    print("   - Swagger docs: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")


if __name__ == "__main__":
    try:
        test_api()
    except requests.ConnectionError:
        print("❌ Error: API not running")
        print("\n   Start the API first:")
        print("   uvicorn api:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

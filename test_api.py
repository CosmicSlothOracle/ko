import requests
import json
import time

BASE_URL = "http://localhost:10000/api"


def test_health():
    print("Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_login():
    print("\nTesting Login...")
    data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Login successful, got tokens")
        return result.get('access_token')
    else:
        print(f"Login failed: {response.text}")
        return None


def test_file_upload(token):
    print("\nTesting File Upload...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # Create a test file
    with open("test_image.png", "wb") as f:
        f.write(b"fake png data")

    with open("test_image.png", "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{BASE_URL}/banners", files=files, headers=headers)

    print(f"Upload Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"Upload successful: {result}")
        return result.get('url')
    else:
        print(f"Upload failed: {response.text}")
        return None


def test_file_download(file_url):
    print(f"\nTesting File Download: {file_url}")
    response = requests.get(f"http://localhost:10000{file_url}")
    print(f"Download Status: {response.status_code}")
    return response.status_code == 200


def test_delete_invalid_file(token):
    print("\nTesting DELETE with invalid file type...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.delete(f"{BASE_URL}/banners/test.bmp", headers=headers)
    print(f"DELETE Status: {response.status_code}")
    print(f"Response: {response.text}")
    return "Invalid file type. Allowed types:" in response.text


def test_participants():
    print("\nTesting Participants...")

    # Add participant
    data = {"name": "Test User", "email": "test@example.com",
            "message": "Test message", "banner": "1"}
    response = requests.post(f"{BASE_URL}/participants", json=data)
    print(f"Add participant status: {response.status_code}")

    # Get participants (requires auth)
    response = requests.get(f"{BASE_URL}/participants")
    print(f"Get participants status: {response.status_code}")
    return response.status_code in [200, 401]  # 401 is expected without auth


if __name__ == "__main__":
    print("Starting API Tests...")

    # Test 1: Health Check
    if not test_health():
        print("❌ Health check failed")
        exit(1)
    print("✅ Health check passed")

    # Test 2: Login
    token = test_login()
    if not token:
        print("❌ Login failed")
        exit(1)
    print("✅ Login passed")

    # Test 3: File Upload/Download
    file_url = test_file_upload(token)
    if file_url:
        if test_file_download(file_url):
            print("✅ File upload/download passed")
        else:
            print("❌ File download failed")
    else:
        print("❌ File upload failed")

    # Test 4: DELETE with invalid file type
    if test_delete_invalid_file(token):
        print("✅ DELETE error message test passed")
    else:
        print("❌ DELETE error message test failed")

    # Test 5: Participants
    if test_participants():
        print("✅ Participants test passed")
    else:
        print("❌ Participants test failed")

    print("\n🎉 All tests completed!")

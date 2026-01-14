import requests
import os

# Base URL - assuming default FastAPI port
BASE_URL = "http://localhost:8002/api/v1"

def test_file_upload():
    # Create a dummy file
    filename = "test_image.txt"
    with open(filename, "w") as f:
        f.write("This is a test file content.")

    try:
        # Upload
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "text/plain")}
            response = requests.post(f"{BASE_URL}/files/upload", files=files)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 201:
            data = response.json()
            print("Upload successful!")
            print(f"File URL: {data.get('url')}")
            
            # Verify file exists (local check since we are on same machine)
            # The URL returned is /static/uploads/...
            # We need to map that to local path
            relative_path = data.get('url').lstrip('/') # remove leading /
            if os.path.exists(relative_path):
                print("File exists on disk.")
            else:
                print(f"File NOT found at {relative_path}")
        else:
            print("Upload failed.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_file_upload()

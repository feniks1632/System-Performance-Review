from fastapi.testclient import TestClient
from app.main import app


def debug_register():
    client = TestClient(app)

    test_data = {
        "email": "debug@test.com",
        "full_name": "Debug User",
        "password": "123456",
        "is_manager": False,
    }

    print("Testing registration with data:")
    print(test_data)

    response = client.post("/api/v1/auth/register", json=test_data)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 400:
        print("❌ Registration failed with 400")
        try:
            error_detail = response.json()
            print(f"Error details: {error_detail}")
        except:
            print("Could not parse error response")


if __name__ == "__main__":
    debug_register()

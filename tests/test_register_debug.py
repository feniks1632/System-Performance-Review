from fastapi.testclient import TestClient
from app.main import app
from app.core.logger import logger


def debug_register():
    client = TestClient(app)

    test_data = {
        "email": "debug@test.com",
        "full_name": "Debug User",
        "password": "123456",
        "is_manager": False,
    }

    logger.info("Testing registration with data:")
    logger.info(test_data)

    response = client.post("/api/v1/auth/register", json=test_data)

    logger.info(f"Status Code: {response.status_code}")
    logger.info(f"Response: {response.text}")

    if response.status_code == 400:
        logger.info("Registration failed with 400")
        try:
            error_detail = response.json()
            logger.info(f"Error details: {error_detail}")
        except:
            logger.info("Could not parse error response")


if __name__ == "__main__":
    debug_register()

def test_fixtures_available(client, test_user_data, test_manager_data):
    """Простой тест чтобы проверить что фикстуры работают"""
    assert client is not None
    assert test_user_data["email"] == "test@example.com"
    assert test_manager_data["is_manager"] == True
    print("All fixtures are working!")

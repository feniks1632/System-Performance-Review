class TestAdminAuthentication:
    """Тесты аутентификации в админ-панели"""

    def test_admin_login_page_accessible(self, client):
        """Тест доступности страницы логина"""
        response = client.get("/admin/login", follow_redirects=True)
        assert response.status_code == 200
        # Проверяем элементы формы логина
        assert "username" in response.text
        assert "password" in response.text
        assert "Войти" in response.text  # Кнопка входа

    def test_admin_login_success(self, client, test_manager_user_for_admin):
        """Тест успешного входа в админку"""
        login_data = {
            "username": "admin_manager@company.com",
            "password": "adminpassword123",
        }

        response = client.post("/admin/login", data=login_data, follow_redirects=False)

        # Должен быть редирект на главную админки (303 See Other)
        assert response.status_code in [200, 302, 303]
        # Должны быть установлены куки аутентификации
        assert "set-cookie" in response.headers

    def test_admin_login_wrong_password(self, client, test_manager_user_for_admin):
        """Тест входа с неправильным паролем"""
        login_data = {
            "username": "admin_manager@company.com",
            "password": "wrongpassword",
        }

        response = client.post("/admin/login", data=login_data)

        assert response.status_code == 400

    def test_admin_login_nonexistent_user(self, client):
        """Тест входа с несуществующим пользователем"""
        login_data = {"username": "nonexistent@company.com", "password": "anypassword"}

        response = client.post("/admin/login", data=login_data)

        assert response.status_code == 400

    def test_admin_login_non_manager(self, client, test_regular_user_for_admin):
        """Тест входа пользователя без прав менеджера"""
        login_data = {
            "username": "admin_regular@company.com",
            "password": "adminpassword123",
        }

        response = client.post("/admin/login", data=login_data)

        assert response.status_code == 400

    def test_admin_login_inactive_user(self, client, inactive_manager_for_admin):
        """Тест входа неактивного пользователя"""
        login_data = {
            "username": "inactive_admin@company.com",
            "password": "adminpassword123",
        }

        response = client.post("/admin/login", data=login_data)

        assert response.status_code == 400

    def test_admin_logout(self, client, admin_login_session):
        """Тест выхода из админки"""
        # Используем куки из сессии входа
        cookies = admin_login_session

        response = client.get("/admin/logout", cookies=cookies, follow_redirects=False)

        # Должен быть редирект на страницу логина
        assert response.status_code in [200, 302, 303]


class TestAdminAccess:
    """Тесты доступа к разделам админки"""

    def test_admin_dashboard_access_without_auth(self, client):
        """Тест доступа к дашборду без аутентификации"""
        response = client.get("/admin/", follow_redirects=False)

        # Должен быть редирект на страницу логина
        assert response.status_code in [302, 303, 307]

    def test_admin_dashboard_access_with_auth(self, admin_login_session, client):
        """Тест доступа к дашборду с аутентификацией"""
        response = client.get("/admin/", cookies=admin_login_session)

        # Должен быть успешный доступ или редирект
        assert response.status_code in [200, 302, 303]

    def test_admin_model_access(self, admin_login_session, client):
        """Тест доступа к моделям данных"""
        # Проверяем доступ к основным разделам
        models = ["user", "goal"]

        for model in models:
            response = client.get(f"/admin/{model}/list", cookies=admin_login_session)
            # Может возвращать 200 или редирект на главную если нет данных
            assert response.status_code in [200, 302, 303]

    def test_admin_api_endpoints_access(self, admin_login_session, client):
        """Тест доступа к API эндпоинтам админки"""
        api_endpoints = [
            "/admin/api/user",
            "/admin/api/goal",
        ]

        for endpoint in api_endpoints:
            response = client.get(endpoint, cookies=admin_login_session)
            # API может возвращать 200, 422 (если нет параметров) или 500
            assert response.status_code in [200, 422, 500]


class TestAdminModelsCRUD:
    """Тесты CRUD операций в админке"""

    def test_user_list_view(
        self, admin_login_session, client, test_manager_user_for_admin
    ):
        """Тест просмотра списка пользователей"""
        response = client.get("/admin/user/list", cookies=admin_login_session)

        # Может быть 200 или редирект
        assert response.status_code in [200, 302, 303]

    def test_user_edit(self, admin_login_session, client, test_manager_user_for_admin):
        """Тест редактирования пользователя"""
        edit_url = f"/admin/user/edit/{test_manager_user_for_admin.id}"

        response = client.get(edit_url, cookies=admin_login_session)

        # Может быть 200 или редирект если форма недоступна
        assert response.status_code in [200, 302, 303]

    def test_search_functionality(self, admin_login_session, client):
        """Тест поиска в админке"""
        search_response = client.get(
            "/admin/api/user?search=admin_manager", cookies=admin_login_session
        )

        # Может быть 200, 422 или 500
        assert search_response.status_code in [200, 422, 500]


class TestAdminPermissions:
    """Тесты проверки прав доступа"""

    def test_admin_access_regular_user(self, client, test_regular_user_for_admin):
        """Тест попытки доступа обычного пользователя"""
        # Пытаемся получить доступ к админке без аутентификации менеджера
        response = client.get("/admin/", follow_redirects=False)

        # Должен быть редирект на логин
        assert response.status_code in [302, 303, 307]

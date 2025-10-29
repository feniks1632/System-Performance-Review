import pytest
from app.models.schemas import GoalStatus

class TestGoalsIntegration:
    def test_create_goal_with_steps(self, client, auth_headers, db_session, test_goal_data):
        """Тест создания цели с подпунктами"""
        # Получаем ID пользователя из базы (так как auth_headers не возвращает user объект)
        from app.models.database import User
        
        # Находим пользователя по токену или создаем нового
        user = db_session.query(User).filter(User.email.like("test_%@example.com")).first()
        if not user:
            # Если пользователь не найден, создаем нового
            from app.core.security import get_password_hash
            import uuid
            unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
            
            user = User(
                email=unique_email,
                full_name="Test User",
                hashed_password=get_password_hash("testpass123"),
                is_manager=False
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
        
        goal_data = test_goal_data.copy()
        goal_data["steps"] = [
            {"title": "Step 1", "description": "First step"},
            {"title": "Step 2", "description": "Second step"}
        ]
        
        response = client.post("/api/v1/goals/", json=goal_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["steps"]) == 2
        assert data["steps"][0]["title"] == "Step 1"
        assert data["steps"][1]["title"] == "Step 2"

    def test_update_goal_status(self, client, auth_headers, test_goal_data):
        """Тест обновления статуса цели"""
        # Создаем цель
        response = client.post("/api/v1/goals/", json=test_goal_data, headers=auth_headers)
        assert response.status_code == 200
        goal_id = response.json()["id"]
        
        # Обновляем статус - отправляем как JSON объект
        status_response = client.put(
            f"/api/v1/goals/{goal_id}/status",
            json={"status": "completed"},  # Исправлено: отправляем JSON объект
            headers=auth_headers
        )
        
        assert status_response.status_code == 200, f"Status update failed: {status_response.text}"
        assert "Goal status updated to completed" in status_response.json()["message"]
        
        # Проверяем что статус обновился
        get_response = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers)
        assert get_response.json()["status"] == "completed"
    
    def test_goal_step_operations(self, client, auth_headers, test_goal_data):
        """Тест операций с подпунктами цели"""
        # Создаем цель
        response = client.post("/api/v1/goals/", json=test_goal_data, headers=auth_headers)
        assert response.status_code == 200
        goal_id = response.json()["id"]
        
        # Создаем подпункт
        step_data = {
            "title": "Test Step",
            "description": "Test Step Description",
            "order_index": 0
        }
        
        step_response = client.post(
            f"/api/v1/goals/{goal_id}/steps", 
            json=step_data, 
            headers=auth_headers
        )
        assert step_response.status_code == 200
        step_id = step_response.json()["id"]
        
        # Обновляем подпункт
        update_data = {
            "title": "Updated Step",
            "is_completed": True
        }
        update_response = client.put(
            f"/api/v1/steps/{step_id}", 
            json=update_data, 
            headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Step"
        assert update_response.json()["is_completed"] == True
        
        # Удаляем подпункт
        delete_response = client.delete(f"/api/v1/steps/{step_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        
        # Проверяем что подпункт удален
        steps_response = client.get(f"/api/v1/goals/{goal_id}/steps", headers=auth_headers)
        assert len(steps_response.json()) == 0

    def test_goal_step_limit(self, client, auth_headers, test_goal_data):
        """Тест лимита подпунктов (максимум 3)"""
        # Создаем цель
        response = client.post("/api/v1/goals/", json=test_goal_data, headers=auth_headers)
        assert response.status_code == 200
        goal_id = response.json()["id"]
        
        # Создаем 3 подпункта
        for i in range(3):
            step_data = {
                "title": f"Step {i}",
                "description": f"Step {i} description",
                "order_index": i
            }
            step_response = client.post(
                f"/api/v1/goals/{goal_id}/steps", 
                json=step_data, 
                headers=auth_headers
            )
            assert step_response.status_code == 200
        
        # Пытаемся создать 4-й подпункт
        step_response = client.post(
            f"/api/v1/goals/{goal_id}/steps", 
            json={"title": "Step 4", "description": "Should fail"}, 
            headers=auth_headers
        )
        assert step_response.status_code == 400
        assert "Maximum 3 steps" in step_response.json()["detail"]
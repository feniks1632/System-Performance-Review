from starlette_admin import DropDown, I18nConfig
from starlette_admin.contrib.sqla import Admin, ModelView

from app.admin.admin_auth import AdminAuthProvider
from app.database.session import engine
from app.models.database import (
    User,
    Goal,
    GoalStep,
    Review,
    RespondentReview,
    Notification,
    QuestionTemplate,
)

auth_provider = AdminAuthProvider()

admin = Admin(
    engine,
    title="Performance Review Admin",
    auth_provider=auth_provider,
    i18n_config=I18nConfig(
        default_locale="ru",
        language_switcher=["ru", "en"],
        language_cookie_name="admin_lang",
    ),
)

# Группировка моделей по логическим разделам
admin.add_view(
    DropDown(
        label="👥 Пользователи",
        views=[
            ModelView(User, label="Пользователь"),
        ],
    )
)

admin.add_view(
    DropDown(
        label="🎯 Цели и задачи",
        views=[
            ModelView(Goal, label="Цель"),
            ModelView(GoalStep, label="Шаг цели"),
        ],
    )
)

admin.add_view(
    DropDown(
        label="📊 Система оценок",
        views=[
            ModelView(Review, label="Оценка"),
            ModelView(RespondentReview, label="Оценка респондента"),
        ],
    )
)

admin.add_view(
    DropDown(
        label="Шаблоны Вопросов",
        views=[ModelView(QuestionTemplate, label="Шаблоны Вопросов")],
    )
)

admin.add_view(
    DropDown(
        label="🔔 Уведомления",
        views=[
            ModelView(Notification, label="Уведомления"),
        ],
    )
)

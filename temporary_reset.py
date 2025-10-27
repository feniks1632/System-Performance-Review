# temporary_reset.py
from app.database.session import engine
from app.models.database import Base

# Удаляем и создаем заново
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Tables recreated!")
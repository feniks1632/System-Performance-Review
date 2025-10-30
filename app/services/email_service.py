import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger
from app.models.database import Goal


class EmailService:
    def __init__(self, db: Session):
        self.db = db

    def send_email(self, to_email: str, subject: str, html_content: str):
        """Базовая отправка email"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{settings.COMPANY_NAME} - {subject}"
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email

            # HTML версия
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #f8f9fa; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                    .footer {{ margin-top: 20px; padding: 20px; background: #f8f9fa; text-align: center; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>{settings.COMPANY_NAME}</h2>
                    </div>
                    <div class="content">
                        {html_content}
                    </div>
                    <div class="footer">
                        <p>Это автоматическое сообщение. Пожалуйста, не отвечайте на него.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_template, "html"))

            # Отправка через SMTP
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def notify_manager_about_pending_review(
        self, goal_id: str, employee_name: str, manager_email: str
    ):
        """Уведомление руководителя о готовности ревью"""
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return False

        subject = "Ожидает ревью"
        html_content = f"""
        <h3>Уведомление о Performance Review</h3>
        <p>Сотрудник <strong>{employee_name}</strong> завершил самооценку по цели и ожидает вашего ревью.</p>
        
        <div style="background: #f8f9fa; padding: 15px; margin: 15px 0;">
            <strong>Цель:</strong> {goal.title}<br>
            <strong>Дедлайн:</strong> {goal.deadline.strftime('%d.%m.%Y') if goal.deadline else 'Не указан'}<br>  
            <strong>Описание:</strong> {goal.description}
        </div>
        
        <p>Пожалуйста, перейдите в систему для завершения процесса оценки:</p>
        <p><a href="{settings.BASE_URL}/goals/{goal_id}" class="button">Перейти к ревью</a></p>
        
        <p>С уважением,<br>Система Performance Review</p>
        """

        return self.send_email(manager_email, subject, html_content)

    def notify_respondents_about_review_request(
        self, goal_id: str, employee_name: str, respondent_emails: list
    ):
        """Уведомление респондентов о запросе оценки"""
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return False

        subject = "Запрос на оценку сотрудника"
        html_content = f"""
        <h3>Запрос на обратную связь</h3>
        <p>Вас просят предоставить обратную связь по работе сотрудника <strong>{employee_name}</strong>.</p>
        
        <div style="background: #f8f9fa; padding: 15px; margin: 15px 0;">
            <strong>Цель для оценки:</strong> {goal.title}<br>
            <strong>Описание:</strong> {goal.description}
        </div>
        
        <p>Пожалуйста, перейдите в систему для заполнения оценки:</p>
        <p><a href="{settings.BASE_URL}/goals/{goal_id}/respondent-review" class="button">Заполнить оценку</a></p>
        
        <p><em>Ваше мнение важно для объективной оценки сотрудника.</em></p>
        
        <p>С уважением,<br>Система Performance Review</p>
        """

        results = []
        for email in respondent_emails:
            results.append(self.send_email(email, subject, html_content))

        return all(results)

    def notify_employee_about_final_review(
        self, goal_id: str, employee_email: str, manager_name: str, final_rating: str
    ):
        """Уведомление сотрудника о завершении ревью"""
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return False

        subject = "Ваше Performance Review завершено"
        html_content = f"""
        <h3>Performance Review завершен</h3>
        <p>Ваш руководитель <strong>{manager_name}</strong> завершил оценку вашей работы.</p>
        
        <div style="background: #f8f9fa; padding: 15px; margin: 15px 0;">
            <strong>Цель:</strong> {goal.title}<br>
            <strong>Итоговый рейтинг:</strong> <span style="font-size: 18px; font-weight: bold;">{final_rating}</span><br>
        </div>
        
        <p>Вы можете ознакомиться с деталями оценки в системе:</p>
        <p><a href="{settings.BASE_URL}/goals/{goal_id}/results" class="button">Посмотреть результаты</a></p>
        
        <p>С уважением,<br>Система Performance Review</p>
        """

        return self.send_email(employee_email, subject, html_content)

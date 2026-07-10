import os
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("SMTP_USERNAME"),
    MAIL_PASSWORD=os.getenv("SMTP_PASSWORD"),
    MAIL_FROM=os.getenv("SMTP_FROM"),
    MAIL_PORT=int(os.getenv("SMTP_PORT", 587)),
    MAIL_SERVER=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

class EmailService:
    @staticmethod
    async def send_invitation_email(email_to: EmailStr, room_name: str, token: str):
        # Envía un correo HTML usando los servidores de Gmail.
        
        invitation_url = f"http://localhost:8000/api/v1/organizations/invitations/accept?token={token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">
                    <h2 style="color: #4F46E5;">¡Te han invitado a unirte a un grupo de estudio!</h2>
                    <p>Hola,</p>
                    <p>Has sido invitado a ser parte de la sala de estudio: <strong>{room_name}</strong> en StudyBuddy.</p>
                    <p>Para aceptar esta invitación y unirte a tus compañeros, haz clic en el siguiente botón (válido por 7 días):</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{invitation_url}" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Aceptar Invitación</a>
                    </div>
                    <p style="font-size: 12px; color: #666;">Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
                    <p style="font-size: 12px; color: #4F46E5; word-break: break-all;">{invitation_url}</p>
                    <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
                    <p style="font-size: 12px; color: #999; text-align: center;">Equipo de StudyBuddy</p>
                </div>
            </body>
        </html>
        """

        message = MessageSchema(
            subject=f"Invitación para unirte a {room_name} - StudyBuddy",
            recipients=[email_to],
            body=html_content,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)

    @staticmethod
    async def send_reset_password_email(email_to: EmailStr, token: str):
        # Envía el correo para reestablecer la contraseña.
        
        reset_url = f"http://localhost:5173/reset-password?token={token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 30px; border-radius: 8px;">
                    <h2 style="color: #333;">Recuperación de contraseña</h2>
                    <p>Hemos recibido una solicitud para cambiar tu contraseña en StudyBuddy.</p>
                    <p>Haz clic en el botón de abajo para asignar una nueva (el enlace caduca en 15 minutos):</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #EF4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Cambiar Contraseña</a>
                    </div>
                    <p style="font-size: 12px; color: #666;">Si no solicitaste este cambio, ignora este correo.</p>
                </div>
            </body>
        </html>
        """

        message = MessageSchema(
            subject="Recupera tu contraseña - StudyBuddy",
            recipients=[email_to],
            body=html_content,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)
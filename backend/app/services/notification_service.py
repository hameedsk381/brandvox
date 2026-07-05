import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def send_sms(to: str, message: str) -> bool:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.info("Twilio not configured — SMS to %s logged instead of sent: %s", to, message)
        return True
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to,
        )
        return True
    except Exception as e:
        logger.error("Failed to send SMS to %s: %s", to, e)
        return False

async def send_email(
    to: str,
    subject: str,
    content: str,
    attachment: Optional[bytes] = None,
    attachment_filename: str = "attachment.pdf",
    attachment_mime_type: str = "application/pdf",
) -> bool:
    if not settings.SENDGRID_API_KEY:
        logger.info("SendGrid not configured — email to %s logged instead of sent: %s", to, subject)
        return True
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL or "noreply@reputationos.ai",
            to_emails=to,
            subject=subject,
            html_content=content,
        )
        if attachment is not None:
            import base64
            from sendgrid.helpers.mail import Attachment, FileContent, FileName, FileType, Disposition
            message.attachment = Attachment(
                FileContent(base64.b64encode(attachment).decode()),
                FileName(attachment_filename),
                FileType(attachment_mime_type),
                Disposition("attachment"),
            )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False

async def send_whatsapp(to: str, message: str) -> bool:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.info("Twilio not configured — WhatsApp to %s logged instead of sent: %s", to, message)
        return True
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        whatsapp_from = settings.TWILIO_WHATSAPP_NUMBER or f"whatsapp:{settings.TWILIO_PHONE_NUMBER}"
        client.messages.create(
            body=message,
            from_=whatsapp_from,
            to=f"whatsapp:{to}",
        )
        return True
    except Exception as e:
        logger.error("Failed to send WhatsApp to %s: %s", to, e)
        return False

def build_review_request_message(business_name: str, review_url: str, employee_name: Optional[str] = None) -> str:
    greeting = f"Hi! {'{name}' if employee_name else ''}"
    body = (
        f"We'd love your feedback! Please take 30 seconds to leave a review for {business_name}.\n\n"
        f"⭐ Leave a review: {review_url}\n\n"
        f"Your feedback helps us improve. Thank you!"
    )
    return body

def build_review_request_email(business_name: str, review_url: str) -> str:
    return f"""
    <html><body style="font-family: Arial, sans-serif; padding: 24px;">
        <h2>How was your experience at {business_name}?</h2>
        <p>We'd really appreciate a quick review. It takes less than 30 seconds.</p>
        <p><a href="{review_url}" style="display: inline-block; padding: 12px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px;">Leave a Review</a></p>
        <p style="color: #666; font-size: 12px;">If the button doesn't work, copy this link: {review_url}</p>
    </body></html>
    """

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr
import resend
from app.core.config import settings


BREVO_API_KEY = settings.BREVO_API_KEY

# -------------------------------------------------
# with custom email template
# -------------------------------------------------


class EmailRecipient(BaseModel):
    email: EmailStr
    name: str = ""


class EmailRawHTMLContent(BaseModel):
    subject: str
    html_content: str
    sender_name: str = "File Management App"
    sender_email: EmailStr = "accounts@filemanagementapp.com"

# -------------------------------------------------
# Using Resend as alternative email service
# -------------------------------------------------
resend.api_key = settings.RESEND_API_KEY

# Single email send
def send_resend_email(
    recipients: List[EmailRecipient],
    content: EmailRawHTMLContent
):
    params: resend.Emails.SendParams = {
        "from": "File management app <onboarding@resend.dev>",
        "to": [r.email for r in recipients],
        "subject": content.subject,
        "html": content.html_content
    }
    email = resend.Emails.send(params)
    return email

# Bulk email send
def send_bulk_resend_email(
    recipients: List[EmailRecipient],
    content: EmailRawHTMLContent
):
    params: List[resend.Emails.SendParams] = [
        {
            "from": f"{content.sender_name} <{content.sender_email}>",
            "to": [r.email],
            "subject": content.subject,
            "html": content.html_content
        } for r in recipients
    ]

    resend.Batch.send(params)

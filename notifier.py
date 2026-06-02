import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def notify_designer(listing: dict, evaluation: dict) -> None:
    """Email designer for approval on items above auto-buy threshold."""
    designer_email = os.environ["DESIGNER_EMAIL"]
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    seller_endpoint = os.environ.get("SELLER_ENDPOINT", "http://localhost:8000")

    title = listing["title"]
    price = listing.get("price", "?")
    url = listing["url"]
    reason = evaluation.get("reason", "")
    confidence = evaluation.get("confidence", 0)

    approve_url = f"{seller_endpoint}/approve?url={url}"
    reject_url = f"{seller_endpoint}/reject?url={url}"

    body = f"""
<h2>Van Gogh Art Match Found</h2>
<p><strong>{title}</strong></p>
<p>Price: <strong>${price}</strong> — above auto-buy threshold</p>
<p>Confidence: {confidence:.0%}</p>
<p>Reason: {reason}</p>
<p>Original listing: <a href="{url}">{url}</a></p>
<br>
<a href="{approve_url}" style="background:#22c55e;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">✅ Approve Purchase</a>
&nbsp;&nbsp;
<a href="{reject_url}" style="background:#ef4444;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">❌ Reject</a>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Art Agent] Approval needed: {title} — ${price}"
    msg["From"] = smtp_user
    msg["To"] = designer_email
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, designer_email, msg.as_string())

    print(f"[notifier] Email sent to {designer_email} for: {title}")

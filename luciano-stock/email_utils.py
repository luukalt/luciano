# email_utils.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_email(subject, body, recipient, pdf_path):
    sender_email = "1.luciano.wassenaar@gmail.com"
    sender_password = "rvcxhxoomrcqmclf" #thyq wfui hmgx fnkz

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with open(pdf_path, "rb") as attachment:
        part = MIMEApplication(attachment.read(), Name=os.path.basename(pdf_path))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
    msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

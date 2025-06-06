import os
import json
import smtplib
import schedule
import time
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from campaign_parser import initialize_state, load_state, update_state, get_today_offset
from campaign_state import load_campaign

# Load environment variables
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Load campaign
campaign = load_campaign("campaign.json")
initialize_state(start_date=datetime.today().strftime("%Y-%m-%d"), email_series=campaign["email_series"])

def generate_prompt(stage, campaign):
    features_text = ", ".join(campaign["features"])
    prompt = (
        f"You are a marketing copywriter.\n"
        f"Write an engaging email for the product '{campaign['product_name']}' aimed at '{campaign['target_audience']}'.\n"
        f"Theme: {stage['theme']}\n"
        f"Objective: {stage['objective']}\n"
        f"Features: {features_text}\n"
        f"The email should be informative, persuasive, and concise.\n"
    )
    return prompt

def generate_and_send_email():
    today_offset = get_today_offset()

    # Check if there's a stage scheduled for today
    stage = next((s for s in campaign["email_series"] if s["day_offset"] == today_offset), None)
    if not stage:
        print(f"No email scheduled for today (offset: {today_offset})")
        return

    state = load_state()
    if today_offset in state["sent_emails"]:
        print(f"Email for offset {today_offset} already sent.")
        return

    prompt = generate_prompt(stage, campaign)
    response = model.generate_content(prompt)
    email_content = response.text

    # Send email to each recipient
    for recipient in campaign["recipients"]:
        msg = EmailMessage()
        msg['Subject'] = f"{stage['theme']} – {campaign['product_name']}"
        msg['From'] = EMAIL_USER
        msg['To'] = recipient
        msg.set_content(email_content)

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.starttls()
                smtp.login(EMAIL_USER, EMAIL_PASS)
                smtp.send_message(msg)
                print(f"Email sent to {recipient} for day offset {today_offset}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {e}")

    # Mark email as sent
    update_state(today_offset)

# Schedule the job to check every day at 9AM
schedule.every().day.at("09:00").do(generate_and_send_email)

print("Scheduler is running... Press Ctrl+C to stop.")
generate_and_send_email()  
while True:
    schedule.run_pending()
    time.sleep(60)


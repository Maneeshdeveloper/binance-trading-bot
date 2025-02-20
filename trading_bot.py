import imaplib
import email
import os
import re
import time
from binance.client import Client

# Binance API Credentials (loaded from GitHub Secrets)
BINANCE_API_KEY = os.getenv("API_KEY")
BINANCE_API_SECRET = os.getenv("API_SECRET")

# Email Credentials (loaded from GitHub Secrets)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Connect to Binance
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Connect to Gmail Inbox
def connect_email():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    return mail

# Extract Latest Email
def fetch_latest_email():
    try:
        mail = connect_email()
        result, data = mail.search(None, "ALL")
        mail_ids = data[0].split()

        if not mail_ids:
            print("No new emails found.")
            return None

        latest_email_id = mail_ids[-1]  # Get the latest email
        result, email_data = mail.fetch(latest_email_id, "(RFC822)")

        raw_email = email_data[0][1].decode("utf-8")
        msg = email.message_from_string(raw_email)
        mail.logout()

        subject = msg["Subject"]
        return subject
    except Exception as e:
        print("Error fetching email:", str(e))
        return None

# Parse Email for Trade Details
def parse_trade_signal(subject):
    try:
        if not subject:
            return None, None, None, None

        # Regex pattern to extract order details
        pattern = r"order (\bBUY\b|\bSELL\b) @ (\d+(?:\.\d+)?) filled on (\w+).*position is (-?\d+)"
        match = re.search(pattern, subject)

        if match:
            order_action = match.group(1)  # BUY or SELL
            contracts = float(match.group(2))  # Lot size
            ticker = match.group(3)  # Symbol (e.g., BTCUSDT)
            position_size = int(match.group(4))  # Position size

            return order_action, contracts, ticker, position_size
        else:
            return None, None, None, None
    except Exception as e:
        print("Error parsing email:", str(e))
        return None, None, None, None

# Place Trade on Binance (Market Order Only)
def place_trade(order_type, contracts, ticker):
    if order_type == "BUY":
        order = client.futures_create_order(
            symbol=ticker,
            side="BUY",
            type="MARKET",
            quantity=contracts
        )
        print(f"✅ BUY order placed: {order}")
    elif order_type == "SELL":
        order = client.futures_create_order(
            symbol=ticker,
            side="SELL",
            type="MARKET",
            quantity=contracts
        )
        print(f"✅ SELL order placed: {order}")
    else:
        print("⚠ No valid trade executed.")

# Main Bot Loop
def main():
    while True:
        print("\n🔍 Checking for new trading signals...")
        email_subject = fetch_latest_email()
        order_action, contracts, ticker, position_size = parse_trade_signal(email_subject)

        if order_action and contracts and ticker:
            print(f"📩 Trade Signal Received: {order_action} {contracts} contracts of {ticker}")
            place_trade(order_action, contracts, ticker)
        else:
            print("⚠ No valid trade signal found.")

        print("⏳ Sleeping for 10 minutes...\n")
        time.sleep(600)  # Check email every 10 minutes

# Run the bot
if __name__ == "__main__":
    main()

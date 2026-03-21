
import os
import sys
from linebot import LineBotApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
if not CHANNEL_ACCESS_TOKEN:
    print("Error: LINE_CHANNEL_ACCESS_TOKEN not found in .env")
    sys.exit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

def clear_rich_menu():
    print("Clearing default Rich Menu...")
    try:
        # Cancel the default rich menu set via API
        line_bot_api.cancel_default_rich_menu()
        print("Successfully canceled default rich menu.")
        print("The Rich Menu configured in LINE Official Account Manager should now be visible.")
    except Exception as e:
        print(f"Error clearing rich menu: {e}")

if __name__ == "__main__":
    clear_rich_menu()

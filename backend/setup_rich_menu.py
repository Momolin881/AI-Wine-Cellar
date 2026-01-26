
import os
import sys
from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds, URIAction, Action
from linebot.models.actions import MessageAction
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
if not CHANNEL_ACCESS_TOKEN:
    print("Error: LINE_CHANNEL_ACCESS_TOKEN not found in .env")
    sys.exit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

def setup_rich_menu():
    print("Setting up Rich Menu...")

    # 1. Define Rich Menu
    rich_menu_to_create = RichMenu(
        size=RichMenuSize(width=2500, height=843), # Compact size (half height)
        selected=True,
        name="Wine Cellar Menu",
        chat_bar_text="開啟選單",
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=1250, height=843),
                action=URIAction(label="我的酒窖", uri=f"https://liff.line.me/{os.getenv('LIFF_ID')}/")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1250, y=0, width=1250, height=843),
                action=URIAction(label="發起聚會", uri=f"https://liff.line.me/{os.getenv('LIFF_ID')}/invitation/create")
            )
        ]
    )

    # 2. Create Rich Menu
    rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)
    print(f"Rich Menu created: {rich_menu_id}")

    # 3. Upload Image
    # Check if image exists, otherwise create a generated one or error
    image_path = "rich_menu_bg.jpg"
    if not os.path.exists(image_path):
        print(f"Warning: {image_path} not found. Please place a 2500x843 image there. Skipping image upload.")
        # We can't set default without image.
        return
    
    with open(image_path, 'rb') as f:
        line_bot_api.set_rich_menu_image(rich_menu_id, "image/jpeg", f)
    print("Rich Menu image uploaded.")

    # 4. Set as Default
    line_bot_api.set_default_rich_menu(rich_menu_id)
    print("Rich Menu set as default.")

if __name__ == "__main__":
    try:
        setup_rich_menu()
    except Exception as e:
        print(f"Error: {e}")

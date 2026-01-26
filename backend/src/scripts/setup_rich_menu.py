
import os
import sys
from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds, URIAction

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.config import settings
except ImportError:
    # Fallback if running from root
    sys.path.append(os.getcwd())
    from src.config import settings

def setup_rich_menu():
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        print("Error: LINE_CHANNEL_ACCESS_TOKEN not set")
        return

    line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)

    # 1. Create Rich Menu Object (Compact Size 2500x843 for 2 buttons setup)
    # User Configuration:
    # Left: Create Invitation (馬上揪喝)
    # Right: My Cellar (我的酒窖)
    
    rich_menu_to_create = RichMenu(
        size=RichMenuSize(width=2500, height=843),
        selected=True,
        name="Wine Cellar Compact Menu",
        chat_bar_text="開啟選單",
        areas=[
            # Button 1: Create Invitation (Left Half)
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=1250, height=843),
                action=URIAction(label='馬上揪喝', uri=f'https://liff.line.me/{settings.LIFF_ID}/invitation/create')
            ),
            # Button 2: My Cellar (Right Half)
            RichMenuArea(
                bounds=RichMenuBounds(x=1250, y=0, width=1250, height=843),
                action=URIAction(label='我的酒窖', uri=f'https://liff.line.me/{settings.LIFF_ID}/')
            )
        ]
    )

    try:
        rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)
        print(f"Rich Menu created: {rich_menu_id}")

        # 2. Upload Image
        # Note: Users managed this manually in LINE Manager, 
        # so we skip auto-upload unless a file is provided.
        image_path = 'rich_menu_bg.jpg'
        if os.path.exists(image_path):
            # Verify image size if strictly following script, 
            # but here we just try to upload if it matches constraints.
            # Compact menu needs 2500x843 image.
            try:
                with open(image_path, 'rb') as f:
                    line_bot_api.set_rich_menu_image(rich_menu_id, "image/jpeg", f)
                print("Image uploaded successfully")
            except Exception as img_err:
                print(f"Image upload failed (might be size mismatch): {img_err}")
        else:
            print("No local image found. Assuming image is set manually or not needed for this script run.")

        # 3. Set as Default
        line_bot_api.set_default_rich_menu(rich_menu_id)
        print("Rich Menu set as default")

    except Exception as e:
        print(f"Failed to setup Rich Menu: {e}")

if __name__ == "__main__":
    setup_rich_menu()

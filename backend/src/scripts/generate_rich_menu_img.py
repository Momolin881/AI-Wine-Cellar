
from PIL import Image, ImageDraw, ImageFont
import os

def create_rich_menu_image(output_path="rich_menu_bg.jpg"):
    # Size: 2500 x 1686 (Large Rich Menu)
    width = 2500
    height = 1686
    
    # Colors
    bg_color = (45, 45, 45) # Dark Gray #2d2d2d
    accent_color = (201, 162, 39) # Gold #c9a227
    text_color = (255, 255, 255)
    line_color = (64, 64, 64)

    # Create Image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw Dividers
    # Horizontal line at split (y=843)
    draw.line([(0, 843), (width, 843)], fill=line_color, width=5)
    # Vertical line in bottom half (x=1250, from y=843 to end)
    draw.line([(1250, 843), (1250, height)], fill=line_color, width=5)

    # Helper to draw centered text (rudimentary since we might not have specific fonts)
    # Trying to load a system font, otherwise default
    try:
        # Mac OS default font
        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 100)
        font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 70)
    except:
        try:
            font_large = ImageFont.truetype("Arial.ttf", 100)
            font_small = ImageFont.truetype("Arial.ttf", 70)
        except:
            # Fallback to default (very small)
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

    # Area 1: Top (My Cellar)
    # Icon/Text placeholder
    # Draw a gold rectangle accent
    draw.rectangle([(1150, 200), (1350, 400)], outline=accent_color, width=10)
    draw.text((1250, 600), "🍷 我的酒窖", fill=text_color, font=font_large, anchor="mm")

    # Area 2: Bottom Left (Create Invitation)
    draw.text((625, 1264), "🥂 發起聚會", fill=accent_color, font=font_small, anchor="mm")

    # Area 3: Bottom Right (Settings)
    draw.text((1875, 1264), "🔔 通知設定", fill=text_color, font=font_small, anchor="mm")

    # Save
    img.save(output_path, quality=90)
    print(f"Image saved to {output_path}")

if __name__ == "__main__":
    create_rich_menu_image()

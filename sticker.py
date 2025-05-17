from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

app = Flask(__name__)

DEFAULT_AVATAR_ID = "900000013"
DEFAULT_BANNER_URL = "https://api.ffcommunity.site/assets/storage/images/StickerAccV2.png"
AVATAR_POSITION = (64, 57)
AVATAR_SIZE = 100
FONT_PATH = os.path.join(os.path.dirname(__file__), "../font.ttf")

def load_image_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except:
        return None

def load_fonts():
    try:
        return {
            "name": ImageFont.truetype(FONT_PATH, 30),
            "uid": ImageFont.truetype(FONT_PATH, 25),
            "guild": ImageFont.truetype(FONT_PATH, 25)
        }
    except:
        return None

def create_sticker(avt_url, name, uid, level, likes, guild_name):
    banner = load_image_from_url(DEFAULT_BANNER_URL)
    if not banner:
        return None

    avatar = load_image_from_url(avt_url)
    fonts = load_fonts()
    if not fonts:
        return None

    sticker = banner.copy()
    draw = ImageDraw.Draw(sticker)

    if avatar:
        avatar = avatar.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
        sticker.paste(avatar, AVATAR_POSITION, avatar)

    draw.text((180, 50), name, font=fonts["name"], fill="black")
    level_text = level if str(level).startswith("Lv") else f"Lv{level}"
    draw.text((45, 160), level_text, font=fonts["name"], fill="black")

    if uid:
        draw.text((284, 161), f"UID: {uid}", font=fonts["uid"], fill="white")
    if likes != "":
        draw.text((360, 120), str(likes), font=fonts["name"], fill="black")
    if guild_name:
        draw.text((300, 10), guild_name, font=fonts["guild"], fill="white")

    return sticker

@app.route("/api/sticker", methods=["GET"])
def generate_banner():
    uid = request.args.get("uid")
    region = request.args.get("region", "sg")
    if not uid:
        return jsonify({"error": "Missing UID"}), 400

    try:
        api_url = f"https://api.ffcommunity.site/api/php/info.php?uid={uid}&region={region}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        if not data.get("AccountName"):
            return jsonify({"error": "Account Does Not Exist"}), 404

        name = data["AccountName"]
        level = data.get("AccountLevel", "Lv.N")
        likes = data.get("AccountLikes", "")
        avatar_id = data.get("AccountAvatarId", DEFAULT_AVATAR_ID)
        guild_name = data.get("Guild Information", {}).get("GuildName")
        if guild_name in (None, "", "Not Found"):
            guild_name = None
    except:
        return jsonify({"error": "Account Does Not Exist"}), 404

    avatar_url = f"https://api.ffcommunity.site/assets/library/icon/pot/{avatar_id}.png"
    sticker = create_sticker(avt_url=avatar_url, name=name, uid=uid, level=level, likes=likes, guild_name=guild_name)
    if not sticker:
        return jsonify({"error": "Failed to generate sticker"}), 500

    output = BytesIO()
    sticker.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype="image/png")

# For Vercel
def handler(environ, start_response):
    return app(environ, start_response)

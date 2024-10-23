from flask import Flask, request, render_template, session
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import base64
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # セッション用のキーを設定

@app.route('/', methods=['GET', 'POST'])
def upload_form():
    # セッションから生成された画像リストを取得、存在しない場合は空リストを作成
    if 'generated_images' not in session:
        session['generated_images'] = []

    generated_images = session['generated_images']

    img_base64_1 = None
    img_base64_2 = None
    text_input_1 = ""
    text_input_2 = ""
    text_input_3 = ""
    text_input_4 = ""
    product_name = ""

    if request.method == 'POST':
        product_name = request.form.get('product_name', '')

        if 'image' in request.files and request.files['image']:
            file = request.files['image']
            img = Image.open(file.stream)
        else:
            return "画像がありません。"

        text_input_1 = request.form.get('text1', '')
        text_input_2 = request.form.get('text2', '')
        text_input_3 = request.form.get('text3', '')
        text_input_4 = request.form.get('text4', '')

        try:
            font_path = "./NotoSansJP-Regular.ttf"
            font_16px = ImageFont.truetype(font_path, 16)
            small_font = ImageFont.truetype(font_path, 10)
        except IOError:
            return "フォントファイルが見つかりません"

        # 1つ目の画像の生成処理
        img_1 = img.copy()
        target_width = 600
        target_height = 350
        img_1.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

        final_width = 800
        final_height = 450
        background_1 = Image.new('RGB', (final_width, final_height), (255, 255, 255))
        img_position = ((final_width - img_1.width) // 2, (final_height - img_1.height) // 2)
        background_1.paste(img_1, img_position)

        if 'logo' in request.files and request.files['logo']:
            logo_file = request.files['logo']
            logo_img = Image.open(logo_file.stream)
        else:
            logo_img = None
        
        if logo_img:
            logo_size = (100, 100)
            logo_img.thumbnail(logo_size, Image.Resampling.LANCZOS)
            background_1.paste(logo_img, (10, 10), logo_img.convert('RGBA'))

        draw_1 = ImageDraw.Draw(background_1)
        draw_1.rectangle([0, 0, final_width - 1, final_height - 1], outline="#eeeeee", width=1)

        def draw_rounded_rectangle(draw, coords, radius, fill):
            x1, y1, x2, y2 = coords
            draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)

        bbox_1 = font_16px.getbbox(text_input_1)
        left_text_width = bbox_1[2] - bbox_1[0]
        left_text_height = bbox_1[3] - bbox_1[1]
        padding = 10
        left_text_background = (10, final_height - left_text_height - padding * 2 - 40, 10 + left_text_width + padding * 2, final_height - 30)
        draw_rounded_rectangle(draw_1, left_text_background, radius=5, fill="#90005D")
        draw_1.text((15 + padding, final_height - left_text_height - padding - 40), text_input_1, font=font_16px, fill="#FFF")

        bbox_center = small_font.getbbox(text_input_2)
        center_text_width = bbox_center[2] - bbox_center[0]
        center_text_position = ((final_width - center_text_width) // 2, final_height - 30)
        draw_1.text(center_text_position, text_input_2, font=small_font, fill="#000")

        img_base64_1 = save_image_with_quality(background_1)

        # 2つ目の画像の生成処理
        img_2 = img.copy()
        target_width_2 = 300
        target_height_2 = 450
        img_2.thumbnail((target_width_2, target_height_2), Image.Resampling.LANCZOS)

        final_width_2 = 495
        final_height_2 = 495
        background_2 = Image.new('RGB', (final_width_2, final_height_2), (255, 255, 255))

        img_position_2 = (final_width_2 - img_2.width - 40, (final_height_2 - img_2.height) // 2)
        background_2.paste(img_2, img_position_2)

        if logo_img:
            background_2.paste(logo_img, (10, 10), logo_img.convert('RGBA'))

        draw_2 = ImageDraw.Draw(background_2)
        draw_2.rectangle([0, 0, final_width_2 - 1, final_height_2 - 1], outline="#eeeeee", width=1)

        bbox_2 = font_16px.getbbox(text_input_1)
        left_text_width_2 = bbox_2[2] - bbox_2[0]
        left_text_height_2 = bbox_2[3] - bbox_2[1]
        left_text_background_2 = (10, final_height_2 - left_text_height_2 - padding * 2 - 50, 10 + left_text_width_2 + padding * 2 + 5, final_height_2 - 45)
        draw_rounded_rectangle(draw_2, left_text_background_2, radius=5, fill="#90005D")
        draw_2.text((15 + padding, final_height_2 - left_text_height_2 - padding - 50), text_input_1, font=font_16px, fill="#FFF")

        img_base64_2 = save_image_with_quality(background_2)

        # 新しい画像を追加
        generated_images.append({
            'product_name': product_name,
            'img_base64_1': img_base64_1,
            'img_base64_2': img_base64_2
        })

        # リストの長さが10を超えたら、古い画像を削除
        if len(generated_images) > 10:
            generated_images.pop(0)

        # セッションに保存
        session['generated_images'] = generated_images

    return render_template('upload_form.html', generated_images=generated_images)


def save_image_with_quality(image, quality=95):
    output = io.BytesIO()
    while True:
        output.seek(0)
        image.save(output, format='JPEG', quality=quality)
        size_in_kb = output.tell() / 1024
        if size_in_kb <= 100 or quality <= 10:
            break
        quality -= 5
    output.seek(0)
    return base64.b64encode(output.getvalue()).decode('utf-8')

if __name__ == '__main__':
    app.run(debug=True)

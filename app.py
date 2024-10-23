from flask import Flask, request, render_template, send_file, make_response
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import base64
import zipfile
import os
from io import BytesIO
from urllib.parse import quote as url_quote


app = Flask(__name__)

generated_images = []  # 生成された画像を保持するリスト

@app.route('/', methods=['GET', 'POST'])
def upload_form():
    global generated_images

    img_base64_1 = None  # 1つ目のプレビュー画像を格納する変数
    img_base64_2 = None  # 2つ目のプレビュー画像を格納する変数
    text_input_1 = ""  # 左下のテキスト
    text_input_2 = ""  # 中央下のテキスト
    text_input_3 = ""  # 右下の上部テキスト
    text_input_4 = ""  # 右下の下部テキスト
    product_name = ""  # 商品名

    if request.method == 'POST' and len(generated_images) < 10:
        # 商品名を取得
        product_name = request.form.get('product_name', '')

        # 画像ファイルを取得
        if 'image' in request.files and request.files['image']:
            file = request.files['image']
            img = Image.open(file.stream)
        else:
            return "画像がありません。"

        # 現在のテキスト入力
        text_input_1 = request.form.get('text1', '')
        text_input_2 = request.form.get('text2', '')
        text_input_3 = request.form.get('text3', '')
        text_input_4 = request.form.get('text4', '')

        # Noto Sans JP フォントファイルのパスを指定する
        try:
            font_path = "./NotoSansJP-Regular.ttf"  # フォントファイルのパス
            font_16px = ImageFont.truetype(font_path, 16)  # 左下と右下のフォントサイズ16px
            small_font = ImageFont.truetype(font_path, 10)  # 小さいフォントサイズ（中央下用）
        except IOError:
            return "フォントファイルが見つかりません"

        # 1つ目の画像を生成（元のサイズで処理）
        img_1 = img.copy()
        target_width = 600
        target_height = 350
        img_1.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

        final_width = 800
        final_height = 450
        background_1 = Image.new('RGB', (final_width, final_height), (255, 255, 255))  # 背景色#fff

        img_position = ((final_width - img_1.width) // 2, (final_height - img_1.height) // 2)
        background_1.paste(img_1, img_position)

        # ロゴ画像を取得（任意）
        if 'logo' in request.files and request.files['logo']:
            logo_file = request.files['logo']
            logo_img = Image.open(logo_file.stream)
        else:
            logo_img = None  # ロゴがアップロードされなかった場合の処理
        
        # 左上にロゴを配置
        if logo_img:
            logo_size = (100, 100)  # ロゴのサイズを指定（必要に応じて調整）
            logo_img.thumbnail(logo_size, Image.Resampling.LANCZOS)  # ロゴのサイズ調整
            background_1.paste(logo_img, (10, 10), logo_img.convert('RGBA'))  # ロゴを左上に貼り付け

        # ボーダー追加
        draw_1 = ImageDraw.Draw(background_1)
        draw_1.rectangle([0, 0, final_width - 1, final_height - 1], outline="#eeeeee", width=1)

        # テキストを描画（1つ目の画像）
        def draw_rounded_rectangle(draw, coords, radius, fill):
            x1, y1, x2, y2 = coords
            draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)

        # 左下にテキスト（背景色#90005D 文字色#fff）
        bbox_1 = font_16px.getbbox(text_input_1)
        left_text_width = bbox_1[2] - bbox_1[0]
        left_text_height = bbox_1[3] - bbox_1[1]
        padding = 10
        left_text_background = (10, final_height - left_text_height - padding * 2 - 40, 10 + left_text_width + padding * 2, final_height - 30)  # 30px上に移動
        draw_rounded_rectangle(draw_1, left_text_background, radius=5, fill="#90005D")
        draw_1.text((15 + padding, final_height - left_text_height - padding - 40), text_input_1, font=font_16px, fill="#FFF")

        # 中央下にテキストを追加（プレビュー1）
        bbox_center = small_font.getbbox(text_input_2)
        center_text_width = bbox_center[2] - bbox_center[0]
        center_text_position = ((final_width - center_text_width) // 2, final_height - 30)
        draw_1.text(center_text_position, text_input_2, font=small_font, fill="#000")

        
        # 右下に縦に2つのテキストを追加（プレビュー1）
        # 1つ目のテキスト（マージン30px）
        bbox_right_1 = font_16px.getbbox(text_input_3)
        right_text_width_1 = bbox_right_1[2] - bbox_right_1[0]
        right_text_height_1 = bbox_right_1[3] - bbox_right_1[1]
        right_text_background_1 = (final_width - right_text_width_1 - 20, final_height - right_text_height_1 - 120, final_width - 10, final_height - 90)

        # 角丸のボーダー付き矩形を描画
        # まずボーダー用の外枠を描画
        draw_rounded_rectangle(draw_1, right_text_background_1, radius=5, fill=None)  # 塗りなしで外枠を描く
        draw_1.rectangle(right_text_background_1, outline="#90005D", width=1)  # ボーダー

        # 次に内側の塗りつぶし部分を描画
        inner_background_1 = (right_text_background_1[0] + 1, right_text_background_1[1] + 1, right_text_background_1[2] - 1, right_text_background_1[3] - 1)
        draw_rounded_rectangle(draw_1, inner_background_1, radius=5, fill="white")  # 塗りつぶし

        # テキストを5px下に移動
        draw_1.text((final_width - right_text_width_1 - 15, final_height - right_text_height_1 - 110), text_input_3, font=font_16px, fill="#90005D")


        # テキストを描画
        draw_1.text((final_width - right_text_width_1 - 15, final_height - right_text_height_1 - 110), text_input_3, font=font_16px, fill="#90005D")

        # 2つ目のテキスト（マージン30px）
        bbox_right_2 = font_16px.getbbox(text_input_4)
        right_text_width_2 = bbox_right_2[2] - bbox_right_2[0]
        right_text_height_2 = bbox_right_2[3] - bbox_right_2[1]
        right_text_background_2 = (final_width - right_text_width_2 - 20, final_height - right_text_height_2 - 55, final_width - 10, final_height - 30)

        # 角丸のボーダー付き矩形を描画
        # まずボーダー用の外枠を描画
        draw_rounded_rectangle(draw_1, right_text_background_2, radius=15, fill=None)  # 塗りなしで外枠を描く
        draw_1.rectangle(right_text_background_2, outline="#90005D", width=1)  # ボーダー

        # 次に内側の塗りつぶし部分を描画
        inner_background_2 = (right_text_background_2[0] + 1, right_text_background_2[1] + 1, right_text_background_2[2] - 1, right_text_background_2[3] - 1)
        draw_rounded_rectangle(draw_1, inner_background_2, radius=15, fill="white")  # 塗りつぶし

        # テキストを描画
        draw_1.text((final_width - right_text_width_2 - 15, final_height - right_text_height_2 - 50), text_input_4, font=font_16px, fill="#90005D")
        # テキストを5px下に移動
        draw_1.text((final_width - right_text_width_2 - 15, final_height - right_text_height_2 - 50), text_input_4, font=font_16px, fill="#90005D")


        # 圧縮とBase64エンコード
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

        img_base64_1 = save_image_with_quality(background_1)

        # 2つ目の画像を生成（同様の処理を適用）
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

        # ボーダー追加
        draw_2 = ImageDraw.Draw(background_2)
        draw_2.rectangle([0, 0, final_width_2 - 1, final_height_2 - 1], outline="#eeeeee", width=1)

        # 左下のテキスト（30px上に）
        bbox_2 = font_16px.getbbox(text_input_1)
        left_text_width_2 = bbox_2[2] - bbox_2[0]
        left_text_height_2 = bbox_2[3] - bbox_2[1]
        left_text_background_2 = (10, final_height_2 - left_text_height_2 - padding * 2 - 50, 10 + left_text_width_2 + padding * 2 + 5, final_height_2 - 45)  # 30px上に
        draw_rounded_rectangle(draw_2, left_text_background_2, radius=5, fill="#90005D")
        draw_2.text((15 + padding, final_height_2 - left_text_height_2 - padding - 50), text_input_1, font=font_16px, fill="#FFF")

        # 右下のテキストを左下テキストの上に配置（プレビュー2）
        # 1つ目の右下テキスト（50px上げる）
        bbox_right_2_1 = font_16px.getbbox(text_input_3)
        right_text_width_2_1 = bbox_right_2_1[2] - bbox_right_2_1[0]
        right_text_height_2_1 = bbox_right_2_1[3] - bbox_right_2_1[1]
        right_text_background_2_1 = (10, final_height_2 - right_text_height_2_1 - padding * 3 - 150, 10 + right_text_width_2_1 + padding * 2, final_height_2 - 150)
        draw_rounded_rectangle(draw_2, right_text_background_2_1, radius=5, fill="white")

        # ボーダー追加
        draw_2.rectangle(right_text_background_2_1, outline="#90005D", width=1)

        # テキストを描画
        draw_2.text((20, final_height_2 - right_text_height_2_1 - padding - 160), text_input_3, font=font_16px, fill="#90005D")

        # 2つ目の右下テキスト（50px上げる）
        bbox_right_2_2 = font_16px.getbbox(text_input_4)
        right_text_width_2_2 = bbox_right_2_2[2] - bbox_right_2_2[0]
        right_text_height_2_2 = bbox_right_2_2[3] - bbox_right_2_2[1]
        right_text_background_2_2 = (10, final_height_2 - right_text_height_2_2 - padding * 3 - 100, 10 +right_text_width_2_2 + padding * 2, final_height_2 - 100)
        draw_rounded_rectangle(draw_2, right_text_background_2_2, radius=5, fill="white")

         # ボーダー追加
        draw_2.rectangle(right_text_background_2_2, outline="#90005D", width=1)

         # テキストを描画
        draw_2.text((20, final_height_2 - right_text_height_2_2 - padding - 110), text_input_4, font=font_16px, fill="#90005D")


        # 中央下のテキスト
        bbox_4 = small_font.getbbox(text_input_2)
        center_text_width_2 = bbox_4[2] - bbox_4[0]
        center_text_position_2 = ((final_width_2 - center_text_width_2) // 2, final_height_2 - 30)
        draw_2.text(center_text_position_2, text_input_2, font=small_font, fill="#000")

        # 圧縮とBase64エンコード
        img_base64_2 = save_image_with_quality(background_2)

        # 生成された画像をリストに追加（ファイル名も保持）
        generated_images.append({
            'product_name': product_name,
            'img_base64_1': img_base64_1,
            'img_base64_2': img_base64_2
        })

    return render_template('upload_form.html', generated_images=generated_images)


@app.route('/download_all', methods=['GET'])
def download_all():
    # すべての生成画像をZIPファイルとしてダウンロード
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, image_data in enumerate(generated_images):
            product_name = image_data['product_name'] or f"image_{i+1}"
            # 1つ目の画像を保存
            img_data_1 = base64.b64decode(image_data['img_base64_1'])
            zip_file.writestr(f"{product_name}_800x450.jpg", img_data_1)
            # 2つ目の画像を保存
            img_data_2 = base64.b64decode(image_data['img_base64_2'])
            zip_file.writestr(f"{product_name}_495x495.jpg", img_data_2)

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name="generated_images.zip")


if __name__ == '__main__':
    app.run(debug=True)

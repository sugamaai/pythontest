from flask import Flask, request, jsonify, url_for, send_file
from PIL import Image
import os
import zipfile
from io import BytesIO
import sys
from pathlib import Path

# 実行ファイルのディレクトリを取得
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
PREVIEW_FOLDER = "static/previews"
OUTPUT_FOLDER = BASE_DIR / "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PREVIEW_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)




# Flaskアプリにテンプレートと静的ファイルのパスを設定
app = Flask(__name__, template_folder=BASE_DIR / "templates", static_folder=BASE_DIR / "static")



@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>画像編集アプリ</title>
        <style>
            .preview img {
                width: 300px;
                margin: 10px;
                border: 1px solid #ccc;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
            }
        </style>
    </head>
    <body>
        <h1>画像編集アプリ</h1>
        <form id="uploadForm" enctype="multipart/form-data">
            <label for="base_image">Base Image:</label>
            <input type="file" name="base_image" id="base_image" required><br><br>
            <label for="qr_images">QR Images :</label>
            <input type="file" name="qr_images" id="qr_images" multiple required><br><br>
            <button type="submit">Upload and Process</button>
        </form>
        <h2>プレビュー:</h2>
        <div class="preview" id="preview"></div>
        <button id="downloadZip" style="display: none;">ZIPとして保存</button>

        <script>
            const form = document.getElementById('uploadForm');
            const previewDiv = document.getElementById('preview');
            const downloadZipButton = document.getElementById('downloadZip');

            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                const formData = new FormData(form);
                
                // APIリクエストを送信
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });
                
                // レスポンスからプレビュー画像を取得
                if (response.ok) {
                    const data = await response.json();
                    previewDiv.innerHTML = ""; // プレビューをリセット
                    const img = document.createElement('img');
                    img.src = data.preview;
                    previewDiv.appendChild(img);

                    // ZIPダウンロードボタンを表示
                    downloadZipButton.style.display = 'block';
                    downloadZipButton.onclick = () => {
                        window.location.href = '/download';
                    };
                } else {
                    alert("エラーが発生しました。");
                }
            });
        </script>
    </body>
    </html>
    """

@app.route('/process', methods=['POST'])
def process_images():
    """アップロード画像を処理してプレビューとZIPダウンロード用データを生成"""
    base_image = request.files.get('base_image')
    qr_files = request.files.getlist('qr_images')

    if not base_image or not qr_files:
        return jsonify({"error": "Base image and QR images are required!"}), 400
    
    if len(qr_files) > 200:
        return jsonify({"error": "You can upload a maximum of 200 QR images."}), 400

    base_image_path = os.path.join(UPLOAD_FOLDER, "base.jpg")
    base_image.save(base_image_path)

    # QR画像を保存
    qr_paths = []
    for qr_file in qr_files:
        qr_path = os.path.join(UPLOAD_FOLDER, qr_file.filename)
        qr_file.save(qr_path)
        qr_paths.append(qr_path)

    # 処理を実行
    output_files, preview_file = generate_images(base_image_path, qr_paths)

    # ZIPファイルを生成
    create_zip(output_files)

    return jsonify({"preview": preview_file})

def generate_images(base_image_path, qr_paths):
    """画像を生成し、最初のプレビュー画像を返す"""
    output_files = []
    preview_file = None


    # 横2列、縦4行の配置を定義
    QR_POSITIONS = [
        (80, 310), (1150, 310),
        (80, 1060), (1150, 1060),
        (80, 1810), (1150, 1810),
        (80, 2560), (1150, 2560)
    ]

    for index, qr_path in enumerate(qr_paths):
        base_img = Image.open(base_image_path).convert("CMYK")
        qr_img = Image.open(qr_path).convert("CMYK").resize((250, 250))

        

        # 規定の位置にQRコードを配置
        for pos in QR_POSITIONS:
            base_img.paste(qr_img, pos)

        # アップロードされたQRコードファイル名を利用して出力ファイル名を生成
        qr_filename = os.path.basename(qr_path)
        qr_name, _ = os.path.splitext(qr_filename)  # 拡張子を除去
        output_name = f"{qr_name}_output.jpg"

        output_path = os.path.join(OUTPUT_FOLDER, output_name)
        base_img.save(output_path, "JPEG")
        output_files.append(output_path)

        # プレビュー用画像（最初の1つだけ保存）
        if preview_file is None:
            preview_path = os.path.join(PREVIEW_FOLDER, output_name)
            base_img.save(preview_path, "JPEG")
            preview_file = url_for('static', filename=f'previews/{output_name}')

    return output_files, preview_file

def create_zip(files):
    """生成された画像をZIPファイルにまとめる"""
    zip_path = os.path.join(OUTPUT_FOLDER, "output_images.zip")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                zip_file.write(file, os.path.basename(file))
        print(f"ZIPファイル生成成功: {zip_path}")
    except Exception as e:
        print(f"ZIPファイル生成失敗: {e}")
    return zip_path


@app.route('/download')
def download_zip():
    """生成されたZIPファイルをダウンロード"""
    zip_path = os.path.join(OUTPUT_FOLDER, "output_images.zip")
    if not os.path.exists(zip_path):
        return jsonify({"error": "ZIPファイルが見つかりません"}), 404
    return send_file(zip_path, mimetype='application/zip', as_attachment=True, download_name="output_images.zip")


if __name__ == "__main__":
    app.run(port=5002)


import os
import base64
import logging
from datetime import datetime, timedelta
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import cv2
import numpy as np
import qrcode

# --- 配置区 ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
MAX_QR_TEXT_LENGTH = 1024

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

logging.basicConfig(level=logging.INFO)

# --- 工具函数区 ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_qr_code(data, version=5, box_size=10, border=4):
    qr = qrcode.QRCode(
        version=version,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def adjust_qr_createtime_param(original_str):
    try:
        parts = original_str.split('&')
        for i in range(len(parts)):
            if parts[i].startswith('createTime='):
                _, time_value = parts[i].split('=', 1)
                dt = datetime.strptime(time_value, "%Y-%m-%dT%H:%M:%S.%f")
                dt += timedelta(hours=1)
                new_time = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                parts[i] = f"createTime={new_time}"
                break
        return '&'.join(parts)
    except Exception as e:
        app.logger.error(f"创建时间调整失败: {str(e)}")
        return original_str

def read_qr_code_from_base64(base64_data):
    try:
        img_bytes = base64.b64decode(base64_data)
        image = Image.open(BytesIO(img_bytes))
        img = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)

        try:
            detect_obj = cv2.wechat_qrcode_WeChatQRCode()
        except Exception as init_error:
            app.logger.error("无法初始化微信二维码识别模型: %s", str(init_error))
            return None

        res = detect_obj.detectAndDecode(img)
        return res[0] if res[0] else None
    except Exception as e:
        app.logger.error(f"二维码解析失败: {str(e)}")
        return None

# --- 路由区 ---
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "未选择文件"

        file = request.files['file']

        if file.filename == '':
            return "文件名为空"
        if not allowed_file(file.filename):
            return "文件类型不合法"

        file_data = file.read()
        encoded_data = base64.b64encode(file_data).decode("utf-8")
        qr_text = read_qr_code_from_base64(encoded_data)

        if qr_text:
            if len(qr_text) > MAX_QR_TEXT_LENGTH:
                return "二维码内容过长，禁止解析"
            return redirect(url_for('show_image', filename='pic', qr_text=qr_text))
        else:
            return "未检测到二维码或读取失败"

    return render_template('index.html')

@app.route('/show/<filename>')
def show_image(filename):
    qr_text = request.args.get('qr_text', '')
    qr_data = request.args.get('data', adjust_qr_createtime_param(qr_text))

    try:
        img = generate_qr_code(qr_data)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return render_template('show.html',
                               qr_text=qr_text,
                               adjusted_text=qr_data,
                               image_data=image_data,
                               filename=filename)

    except Exception as e:
        app.logger.error(f"二维码生成失败: {str(e)}")
        return "二维码生成失败", 500

# --- 启动区 ---
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)

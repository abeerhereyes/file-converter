from flask import Flask, request, send_file,  jsonify
from flask_cors import CORS
from io import BytesIO
import os
import subprocess
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_path


app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {
    'txt', 'pdf', 'docx', 'xlsx', 'pptx', 'jpg', 'jpeg', 'png', 'gif',
    # Video formats
    'mp4', 'm4v', 'mp4v', '3gp', '3g2', 'avi', 'mov', 'wmv', 'mkv',
    'flv', 'ogv', 'webm', 'h264', '264', 'hevc', '265',
    # Audio formats
    'mp3', 'wav', 'ogg', 'aac', 'wma', 'flac', 'm4a'
}


VIDEO_FORMATS = {
    'mp4', 'm4v', 'mp4v', '3gp', '3g2', 'avi', 'mov', 'wmv', 
    'mkv', 'flv', 'ogv', 'webm', 'h264', '264', 'hevc', '265'
}

AUDIO_FORMATS = {
    'mp3', 'wav', 'ogg', 'aac', 'wma', 'flac', 'm4a'
}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    target_format = request.form.get('format')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        input_format = filename.rsplit('.', 1)[1].lower()

        try:
            # Handle video conversions
            if target_format in VIDEO_FORMATS:
                if input_format in VIDEO_FORMATS:
                    return convert_video(filepath, target_format)
                else:
                    return jsonify({'error': 'Input file must be a video format'}), 400

            # Handle audio conversions
            elif target_format in AUDIO_FORMATS:
                if input_format in AUDIO_FORMATS:
                    return convert_audio(filepath, target_format)
                elif input_format in VIDEO_FORMATS:
                    return extract_audio(filepath, target_format)
                else:
                    return jsonify({'error': 'Input file must be an audio or video format'}), 400

            # Handle existing conversion types
            elif target_format == 'pdf':
                if filename.endswith('.txt'):
                    return convert_txt_to_pdf(filepath)
                elif filename.endswith(('.jpg', '.jpeg', '.png')):
                    return convert_image_to_pdf(filepath)
                else:
                    return jsonify({'error': 'Unsupported file type for PDF conversion'}), 400

            elif target_format in ['jpg', 'png']:
                if filename.endswith('.pdf'):
                    return convert_pdf_to_image(filepath, target_format)
                else:
                    return jsonify({'error': 'Unsupported file type for image conversion'}), 400

            elif target_format == 'txt':
                if filename.endswith('.pdf'):
                    return convert_pdf_to_txt(filepath)
                else:
                    return jsonify({'error': 'Unsupported file type for text conversion'}), 400

            else:
                return jsonify({'error': 'Unsupported conversion format'}), 400

        except Exception as e:
            return jsonify({'error': f'Conversion error: {str(e)}'}), 500

        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)

    return jsonify({'error': 'Invalid file type'}), 400

def convert_video(input_path, target_format):
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'converted.{target_format}')
    
    try:
        # Use ffmpeg to convert the video
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264' if target_format not in ['webm', 'ogv'] else 'libvpx',
            '-c:a', 'aac' if target_format not in ['webm', 'ogv'] else 'libvorbis',
            '-strict', '-2',
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        with open(output_path, 'rb') as f:
            data = BytesIO(f.read())
        
        os.remove(output_path)
        return send_file(
            data,
            as_attachment=True,
            download_name=f'converted.{target_format}',
            mimetype=f'video/{target_format}'
        )
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg error: {e.stderr.decode()}")

def convert_audio(input_path, target_format):
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'converted.{target_format}')
    
    try:
        # Use ffmpeg to convert the audio
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vn',  # No video
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        with open(output_path, 'rb') as f:
            data = BytesIO(f.read())
        
        os.remove(output_path)
        return send_file(
            data,
            as_attachment=True,
            download_name=f'converted.{target_format}',
            mimetype=f'audio/{target_format}'
        )
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg error: {e.stderr.decode()}")

def extract_audio(input_path, target_format):
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'converted.{target_format}')
    
    try:
    
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vn',               # Remove any video stream
            '-acodec', 'libmp3lame' if target_format == 'mp3'
                      else 'libvorbis' if target_format == 'ogg'
                      else 'aac' if target_format == 'aac'
                      else target_format,
            '-ar', '44100',      # Audio sample rate
            '-ab', '192k',       # Audio bitrate
            '-y',                # Overwrite output file if it exists
            output_path
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            raise Exception("Output file was not created")
            
        with open(output_path, 'rb') as f:
            data = BytesIO(f.read())
        
        os.remove(output_path)
        
        return send_file(
            data,
            as_attachment=True,
            download_name=f'converted.{target_format}',
            mimetype=f'audio/{target_format}'
        )
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error in video")
    except Exception as e:
   
        raise Exception("Error in video")

def convert_txt_to_pdf(filepath):
    with open(filepath, 'r') as f:
        text = f.read()

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer)
    text_lines = text.split('\n')
    y = 750
    for line in text_lines:
        pdf.drawString(100, y, line)
        y -= 12
    pdf.save()
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer, 
        as_attachment=True, 
        download_name='converted.pdf', 
        mimetype='application/pdf'
    )

def convert_image_to_pdf(filepath):
    image = Image.open(filepath)
    pdf_buffer = BytesIO()
    image.save(pdf_buffer, format="PDF")
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer, 
        as_attachment=True, 
        download_name='converted.pdf', 
        mimetype='application/pdf'
    )

def convert_pdf_to_image(filepath, target_format):
    images = convert_from_path(filepath)
    img_buffer = BytesIO()
    images[0].save(img_buffer, format=target_format.upper())
    img_buffer.seek(0)
    return send_file(
        img_buffer, 
        as_attachment=True, 
        download_name=f'converted.{target_format}', 
        mimetype=f'image/{target_format}'
    )

def convert_pdf_to_txt(filepath):
    reader = PdfReader(filepath)
    text = ''
    for page in reader.pages:
        text += page.extract_text()

    txt_buffer = BytesIO()
    txt_buffer.write(text.encode('utf-8'))
    txt_buffer.seek(0)
    return send_file(
        txt_buffer, 
        as_attachment=True, 
        download_name='converted.txt', 
        mimetype='text/plain'
    )

@app.route('/cleanup', methods=['POST'])
def cleanup_upload_folder():
    folder = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            return jsonify({'error': f'Error deleting {filename}: {str(e)}'}), 500
    return jsonify({'message': 'Upload folder cleaned successfully!'}), 200

if __name__ == '__main__':
    app.run(debug=True)
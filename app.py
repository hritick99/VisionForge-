"""
Flask Web Application for AI Vision Image Analysis
Run: python app.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
import os
import base64
from pathlib import Path
from werkzeug.utils import secure_filename

# pip install flask openai anthropic

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create uploads folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_with_gpt4o(image_path, prompt):
    """Analyze image using GPT-4o"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {"error": "OpenAI API key not set"}
        
        client = OpenAI(api_key=api_key)
        base64_image = encode_image(image_path)
        
        ext = Path(image_path).suffix.lower()
        media_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', 
                      '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
        media_type = media_types.get(ext, 'image/jpeg')
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        return {"success": True, "analysis": response.choices[0].message.content}
        
    except Exception as e:
        return {"error": str(e)}

def analyze_with_claude(image_path, prompt):
    """Analyze image using Claude"""
    try:
        import anthropic
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "Anthropic API key not set"}
        
        client = anthropic.Anthropic(api_key=api_key)
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        ext = Path(image_path).suffix.lower()
        media_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', 
                      '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
        media_type = media_types.get(ext, 'image/jpeg')
        
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt}
                    ],
                }
            ],
        )
        
        return {"success": True, "analysis": message.content[0].text}
        
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Get parameters
    model = request.form.get('model', 'gpt4o')
    analysis_type = request.form.get('analysis_type', 'detailed')
    
    # Define prompts
    prompts = {
        "detailed": """Analyze this image in comprehensive detail:
1. Main subjects, objects, and people
2. Scene setting and environment
3. Colors, lighting, and composition
4. Mood and atmosphere
5. Any visible text
6. Notable details
7. Context and purpose""",
        
        "story": """Create a rich, engaging story based on this image. 
Include vivid descriptions, character backgrounds, emotions, and what might happen next.""",
        
        "technical": """Provide expert technical analysis:
- Composition techniques
- Lighting quality and setup
- Color grading and palette
- Depth of field
- Camera settings estimation
- Professional photography principles""",
        
        "creative": """Deep creative analysis:
- Artistic style and influences
- Symbolism and metaphors
- Emotional impact
- Cultural context
- Potential interpretations"""
    }
    
    prompt = prompts.get(analysis_type, prompts["detailed"])
    
    # Analyze with selected model
    if model == 'gpt4o':
        result = analyze_with_gpt4o(filepath, prompt)
    elif model == 'claude':
        result = analyze_with_claude(filepath, prompt)
    else:
        result = {"error": "Invalid model selected"}
    
    # Clean up uploaded file
    try:
        os.remove(filepath)
    except:
        pass
    
    return jsonify(result)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Vision Image Analyzer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .upload-section {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 20px;
        }
        .upload-section:hover { background: #f8f9ff; border-color: #764ba2; }
        .upload-icon { font-size: 60px; margin-bottom: 15px; }
        input[type="file"] { display: none; }
        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        select, button {
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #667eea;
            font-size: 16px;
            font-family: inherit;
        }
        select { background: white; cursor: pointer; }
        button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .preview {
            display: none;
            margin: 20px 0;
            text-align: center;
        }
        .preview img {
            max-width: 100%;
            max-height: 400px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .result {
            display: none;
            background: #f8f9ff;
            padding: 30px;
            border-radius: 15px;
            margin-top: 20px;
            line-height: 1.8;
            color: #333;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
            color: #667eea;
            font-size: 18px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            background: #ffe6e6;
            color: #d32f2f;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 AI Vision Image Analyzer</h1>
        
        <div class="upload-section" id="uploadSection">
            <div class="upload-icon">📷</div>
            <div>
                <strong>Click to upload</strong> or drag and drop<br>
                PNG, JPG, GIF, WEBP (max 16MB)
            </div>
            <input type="file" id="fileInput" accept="image/*">
        </div>
        
        <div class="preview" id="preview">
            <img id="previewImg" src="" alt="Preview">
        </div>
        
        <div class="controls">
            <select id="modelSelect">
                <option value="gpt4o">GPT-4o (OpenAI)</option>
                <option value="claude">Claude Sonnet 4.5 (Anthropic)</option>
            </select>
            
            <select id="analysisType">
                <option value="detailed">Detailed Analysis</option>
                <option value="story">Generate Story</option>
                <option value="technical">Technical Analysis</option>
                <option value="creative">Creative Analysis</option>
            </select>
        </div>
        
        <button id="analyzeBtn" disabled>🔍 Analyze Image</button>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div>Analyzing your image with AI...</div>
        </div>
        
        <div class="error" id="error"></div>
        <div class="result" id="result"></div>
    </div>

    <script>
        const uploadSection = document.getElementById('uploadSection');
        const fileInput = document.getElementById('fileInput');
        const preview = document.getElementById('preview');
        const previewImg = document.getElementById('previewImg');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        const error = document.getElementById('error');
        
        let selectedFile = null;
        
        uploadSection.addEventListener('click', () => fileInput.click());
        
        uploadSection.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadSection.style.background = '#f0f0ff';
        });
        
        uploadSection.addEventListener('dragleave', () => {
            uploadSection.style.background = '';
        });
        
        uploadSection.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadSection.style.background = '';
            if (e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0]);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
        
        function handleFile(file) {
            if (!file.type.startsWith('image/')) {
                showError('Please upload an image file');
                return;
            }
            
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                preview.style.display = 'block';
                analyzeBtn.disabled = false;
                result.style.display = 'none';
                error.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }
        
        analyzeBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            const formData = new FormData();
            formData.append('image', selectedFile);
            formData.append('model', document.getElementById('modelSelect').value);
            formData.append('analysis_type', document.getElementById('analysisType').value);
            
            loading.style.display = 'block';
            result.style.display = 'none';
            error.style.display = 'none';
            analyzeBtn.disabled = true;
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                loading.style.display = 'none';
                analyzeBtn.disabled = false;
                
                if (data.error) {
                    showError(data.error);
                } else {
                    result.textContent = data.analysis;
                    result.style.display = 'block';
                }
            } catch (err) {
                loading.style.display = 'none';
                analyzeBtn.disabled = false;
                showError('Network error: ' + err.message);
            }
        });
        
        function showError(message) {
            error.textContent = message;
            error.style.display = 'block';
        }
    </script>
</body>
</html>
'''

# Save HTML template
@app.before_request
def create_template():
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(template_dir, exist_ok=True)
    with open(os.path.join(template_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("AI VISION IMAGE ANALYZER")
    print("="*60)
    print("\nStarting server...")
    print("Open your browser to: http://localhost:5000")
    print("\nMake sure to set your API keys:")
    print("  export OPENAI_API_KEY='your-key'")
    print("  export ANTHROPIC_API_KEY='your-key'")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
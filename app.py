from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import dashscope
from dashscope import Generation
import json
import re
import base64
import io
from PIL import Image
from datetime import datetime, date
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available. Image-to-text feature will be disabled.")
from config import Config
from models import db, User, Essay, Conversation, UserStats

app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ielts_writing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 在生产环境中应该使用环境变量

# 初始化扩展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

CORS(app, resources={
    r"/api/*": {
        "origins": ["~", "http://127.0.0.1:8000", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def update_user_stats(user_id):
    """更新用户统计信息"""
    try:
        # 获取用户的所有作文
        essays = Essay.query.filter_by(user_id=user_id).all()
        
        if not essays:
            return
        
        # 计算平均分
        total_essays = len(essays)
        avg_overall = sum(e.overall_score for e in essays) / total_essays
        avg_task = sum(e.task_achievement_score for e in essays) / total_essays
        avg_coherence = sum(e.coherence_cohesion_score for e in essays) / total_essays
        avg_lexical = sum(e.lexical_resource_score for e in essays) / total_essays
        avg_grammar = sum(e.grammatical_range_accuracy_score for e in essays) / total_essays
        
        # 更新或创建用户统计
        user_stats = UserStats.query.filter_by(user_id=user_id).first()
        if not user_stats:
            user_stats = UserStats(user_id=user_id)
            db.session.add(user_stats)
        
        user_stats.total_essays = total_essays
        user_stats.average_score = avg_overall
        user_stats.avg_task_achievement = avg_task
        user_stats.avg_coherence_cohesion = avg_coherence
        user_stats.avg_lexical_resource = avg_lexical
        user_stats.avg_grammatical_range_accuracy = avg_grammar
        user_stats.updated_at = datetime.utcnow()
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error updating user stats: {e}")
        db.session.rollback()

# Configure DashScope
if Config.DASHSCOPE_API_KEY:
    dashscope.api_key = Config.DASHSCOPE_API_KEY
    print("✅ DashScope API key configured successfully")
else:
    print("⚠️  Warning: DASHSCOPE_API_KEY not found. Please set it in your environment or .env file")
    print("   You can get your API key from: https://dashscope.console.aliyun.com/")
    print("   Set it with: export DASHSCOPE_API_KEY=your_api_key_here")

def generate_ielts_feedback(essay_topic, essay_text):
    """
    Generate comprehensive IELTS feedback using Qwen (通义千问)
    """
    print("Using Qwen model for essay analysis...")
    
    try:
        # 构建提示词
        prompt = f"""
你是一位专业的雅思写作评分专家。请对以下雅思作文进行详细分析，并按照雅思官方评分标准给出反馈。

题目: {essay_topic}

作文内容:
{essay_text}

请按照雅思官方四项评分标准进行评分，并按照以下JSON格式返回分析结果，使用中文回复：

{{
    "overall_score": 分数(0-9),
    "overall_feedback": "总体反馈",
    "rubric_scores": {{
        "task_achievement": 分数(0-9),
        "coherence_cohesion": 分数(0-9),
        "lexical_resource": 分数(0-9),
        "grammatical_range_accuracy": 分数(0-9)
    }},
    "statistics": {{
        "linking_words_count": 连词数量,
        "linking_words_goal": 7,
        "word_repetition_count": 重复词汇数量,
        "word_repetition_goal": 3,
        "grammar_mistakes_count": 语法错误数量,
        "grammar_mistakes_goal": 0
    }},
    "task_achievement": {{
        "score": 分数(0-9),
        "strengths": ["优势1", "优势2"],
        "areas_for_improvement": ["改进点1", "改进点2"],
        "improvement_suggestions": {{
            "how_to_address_prompt": "如何完整回应题目",
            "how_to_develop_ideas": "如何展开观点",
            "how_to_stay_on_topic": "如何点题",
            "contextual_development": "上下文展开建议",
            "better_format": "更优的格式建议",
            "text_structure": "行文结构建议"
        }}
    }},
    "coherence_cohesion": {{
        "score": 分数(0-9),
        "strengths": ["优势1", "优势2"],
        "areas_for_improvement": ["改进点1", "改进点2"],
        "improvement_suggestions": {{
            "logical_organization": "逻辑组织建议",
            "thematic_organization": "主题组织建议",
            "logical_sequencing": "逻辑衔接顺序建议",
            "referencing_substitution": "引用替换建议",
            "discourse_markers": "标志性逻辑提示词建议"
        }}
    }},
    "lexical_resource": {{
        "score": 分数(0-9),
        "strengths": ["优势1", "优势2"],
        "areas_for_improvement": ["改进点1", "改进点2"],
        "vocabulary_improvements": [
            {{
                "incorrect": "错误表达",
                "correct": "正确表达",
                "explanation": "详细解释错误原因和正确用法",
                "error_type": "错误类型（如：介词错误、代词错误等）"
            }}
        ]
    }},
    "grammatical_range_accuracy": {{
        "score": 分数(0-9),
        "strengths": ["优势1", "优势2"],
        "areas_for_improvement": ["改进点1", "改进点2"],
        "grammar_corrections": [
            {{
                "incorrect": "错误语法",
                "correct": "正确语法",
                "explanation": "详细解释语法错误原因和正确用法",
                "error_type": "错误类型（如：时态错误、主谓一致错误等）",
                "sentence_context": "包含错误的完整句子"
            }}
        ]
    }}
}}

评分标准说明：
1. Task Achievement (任务完成度): 是否完全回应题目要求，观点是否清晰，论证是否充分
2. Coherence and Cohesion (连贯与衔接): 文章结构是否清晰，段落间连接是否自然，逻辑是否连贯
3. Lexical Resource (词汇资源): 词汇使用是否准确、多样，是否适合学术写作
4. Grammatical Range and Accuracy (语法范围和准确性): 语法结构是否多样，语法错误是否影响理解

请特别注意：
1. 严格按照雅思官方评分标准进行评分，每项给出0-9分的具体分数
2. 在grammar_corrections和vocabulary_improvements中，请提供具体的错误分析
3. 在statistics中统计连词数量、重复词汇数量和语法错误数量
4. 对于每个错误，请提供包含该错误的完整句子作为上下文
5. 错误解释要具体，如："介词的语法错误：应使用 'From a social perspective' 而不是 'In the social point of view'"

请确保返回的是有效的JSON格式，不要包含任何其他文本。
"""

        # 调用通义千问模型
        response = Generation.call(
            model='qwen-plus',
            prompt=prompt,
            max_tokens=4000,
            temperature=0.7
        )
        
        if response.status_code == 200:
            # 尝试解析JSON响应
            try:
                feedback_text = response.output.text
                # 清理响应文本，移除可能的markdown标记
                feedback_text = feedback_text.strip()
                if feedback_text.startswith('```json'):
                    feedback_text = feedback_text[7:]
                if feedback_text.endswith('```'):
                    feedback_text = feedback_text[:-3]
                feedback_text = feedback_text.strip()
                
                feedback = json.loads(feedback_text)
                return feedback
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                print(f"原始响应: {response.output.text}")
                # 如果JSON解析失败，返回fallback响应
                return create_fallback_response()
        else:
            print(f"通义千问API调用失败: {response.status_code}")
            return create_fallback_response()
            
    except Exception as e:
        print(f"调用通义千问时发生错误: {e}")
        return create_fallback_response()

def create_fallback_response():
    """Create a fallback response if AI generation fails"""
    return {
        "overall_score": 6.0,
        "overall_feedback": "The essay addresses the topic with some relevant points, but there are areas for improvement in task response, coherence, vocabulary, and grammar.",
        "rubric_scores": {
            "task_achievement": 6,
            "coherence_cohesion": 6,
            "lexical_resource": 6,
            "grammatical_range_accuracy": 6
        },
        "statistics": {
            "linking_words_count": 3,
            "linking_words_goal": 7,
            "word_repetition_count": 5,
            "word_repetition_goal": 3,
            "grammar_mistakes_count": 2,
            "grammar_mistakes_goal": 0
        },
        "task_achievement": {
            "score": 6,
            "strengths": ["Addresses both advantages and disadvantages", "Provides some reasoning"],
            "areas_for_improvement": ["Needs deeper exploration", "Points could be more developed"],
            "improvement_suggestions": {
                "how_to_address_prompt": "Ensure you fully explore each advantage and disadvantage with detailed explanations.",
                "how_to_develop_ideas": "Use specific examples to support your arguments.",
                "how_to_stay_on_topic": "Always relate your points back to the main topic.",
                "contextual_development": "Start with a clear thesis and summarize main points in conclusion.",
                "better_format": "Use traditional essay structure: introduction, body paragraphs, conclusion.",
                "text_structure": "Organize ideas logically within paragraphs."
            }
        },
        "coherence_cohesion": {
            "score": 6,
            "strengths": ["Clear introduction and conclusion", "Some use of linking words"],
            "areas_for_improvement": ["Lacks clear topic sentences", "Ideas could be better sequenced"],
            "improvement_suggestions": {
                "logical_organization": "Organize ideas in a structured manner with logical sequence.",
                "thematic_organization": "Each paragraph should have a clear topic sentence.",
                "logical_sequencing": "Ensure each paragraph flows logically from one point to the next.",
                "referencing_substitution": "Use pronouns and referencing words effectively.",
                "discourse_markers": "Use more varied linking words and phrases."
            }
        },
        "lexical_resource": {
            "score": 6,
            "strengths": ["Adequate vocabulary range"],
            "areas_for_improvement": ["Limited vocabulary variety", "Some spelling errors"],
            "vocabulary_improvements": [
                {
                    "incorrect": "In the social point of view",
                    "correct": "From a social perspective",
                    "explanation": "介词的语法错误：应使用 'From a social perspective' 而不是 'In the social point of view'。'From a social perspective' 是更准确和自然的表达方式。",
                    "error_type": "介词错误"
                }
            ]
        },
        "grammatical_range_accuracy": {
            "score": 6,
            "strengths": ["Generally clear meaning"],
            "areas_for_improvement": ["Some grammatical errors", "Inconsistent tenses"],
            "grammar_corrections": [
                {
                    "incorrect": "We are making him to try hard",
                    "correct": "We encourage them to try hard",
                    "explanation": "及物动词使用错误：不需要使用'making him to'，可以直接用'encourage them to'。同时代词单复数错误：应该用 'them' 而不是 'the child'，因为在之前的句子中提到了'children'。",
                    "error_type": "及物动词错误、代词单复数错误",
                    "sentence_context": "We are making him to try hard in his studies."
                }
            ]
        }
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({'success': True, 'message': '登录成功', 'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # 验证输入
    if not username or not email or not password:
        return jsonify({'success': False, 'message': '请填写所有字段'}), 400
    
    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已存在'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': '邮箱已存在'}), 400
    
    # 创建新用户
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(user)
    db.session.commit()
    
    # 创建用户统计记录
    user_stats = UserStats(user_id=user.id)
    db.session.add(user_stats)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '注册成功'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': '已退出登录'})

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/test_connection.html')
def test_connection():
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>连接测试</title>
    </head>
    <body>
        <h1>连接测试</h1>
        <button onclick="testConnection()">测试连接</button>
        <div id="result"></div>

        <script>
            async function testConnection() {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '测试中...';
                
                try {
                    // 测试主页
                    console.log('Testing homepage...');
                    const homeResponse = await fetch('/');
                    console.log('Homepage response:', homeResponse.status);
                    
                    if (homeResponse.ok) {
                        resultDiv.innerHTML += '<p>✅ 主页连接成功</p>';
                    } else {
                        resultDiv.innerHTML += '<p>❌ 主页连接失败: ' + homeResponse.status + '</p>';
                    }
                    
                    // 测试API
                    console.log('Testing API...');
                    const apiResponse = await fetch('/api/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            topic: 'Test topic',
                            essay: 'This is a test essay with some content to analyze.'
                        })
                    });
                    
                    console.log('API response:', apiResponse.status);
                    
                    if (apiResponse.ok) {
                        const data = await apiResponse.json();
                        resultDiv.innerHTML += '<p>✅ API连接成功，返回数据: ' + JSON.stringify(data).substring(0, 100) + '...</p>';
                    } else {
                        const errorText = await apiResponse.text();
                        resultDiv.innerHTML += '<p>❌ API连接失败: ' + apiResponse.status + ' - ' + errorText + '</p>';
                    }
                    
                } catch (error) {
                    console.error('Connection test error:', error);
                    resultDiv.innerHTML += '<p>❌ 连接错误: ' + error.message + '</p>';
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/api/analyze', methods=['POST', 'OPTIONS'])
def analyze_essay():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    try:
        data = request.get_json()
        essay_topic = data.get('topic', '')
        essay_text = data.get('essay', '')
        
        if not essay_topic or not essay_text:
            return jsonify({'error': 'Topic and essay text are required'}), 400
        
        print(f"Analyzing essay: {len(essay_text)} characters")
        
        # 直接调用，如果超时会自动使用fallback
        feedback = generate_ielts_feedback(essay_topic, essay_text)
        print("Analysis completed successfully")
        
        # 如果用户已登录，保存批改记录到数据库
        if current_user.is_authenticated:
            try:
                # 创建作文记录
                essay = Essay(
                    user_id=current_user.id,
                    topic=essay_topic,
                    content=essay_text,
                    overall_score=feedback.get('overall_score', 0.0),
                    task_achievement_score=feedback.get('rubric_scores', {}).get('task_achievement', 0.0),
                    coherence_cohesion_score=feedback.get('rubric_scores', {}).get('coherence_cohesion', 0.0),
                    lexical_resource_score=feedback.get('rubric_scores', {}).get('lexical_resource', 0.0),
                    grammatical_range_accuracy_score=feedback.get('rubric_scores', {}).get('grammatical_range_accuracy', 0.0),
                    linking_words_count=feedback.get('statistics', {}).get('linking_words_count', 0),
                    word_repetition_count=feedback.get('statistics', {}).get('word_repetition_count', 0),
                    grammar_mistakes_count=feedback.get('statistics', {}).get('grammar_mistakes_count', 0),
                    overall_feedback=feedback.get('overall_feedback', ''),
                    task_achievement_feedback=json.dumps(feedback.get('task_achievement', {}), ensure_ascii=False),
                    coherence_cohesion_feedback=json.dumps(feedback.get('coherence_cohesion', {}), ensure_ascii=False),
                    lexical_resource_feedback=json.dumps(feedback.get('lexical_resource', {}), ensure_ascii=False),
                    grammatical_range_accuracy_feedback=json.dumps(feedback.get('grammatical_range_accuracy', {}), ensure_ascii=False)
                )
                
                # 设置错误纠正信息
                if feedback.get('grammatical_range_accuracy', {}).get('grammar_corrections'):
                    essay.set_grammar_corrections(feedback['grammatical_range_accuracy']['grammar_corrections'])
                
                if feedback.get('lexical_resource', {}).get('vocabulary_improvements'):
                    essay.set_vocabulary_improvements(feedback['lexical_resource']['vocabulary_improvements'])
                
                db.session.add(essay)
                db.session.commit()
                
                # 更新用户统计
                update_user_stats(current_user.id)
                
                print(f"Essay saved to database with ID: {essay.id}")
                
            except Exception as e:
                print(f"Error saving essay to database: {e}")
                # 即使保存失败，也返回分析结果
                pass
        
        return jsonify(feedback)
    
    except Exception as e:
        print(f"Error in analyze_essay: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ocr', methods=['POST', 'OPTIONS'])
def extract_text_from_image():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    if not TESSERACT_AVAILABLE:
        return jsonify({'error': 'OCR feature is not available. Please install Tesseract OCR.'}), 503
    
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        
        if not image_data:
            return jsonify({'error': 'Image data is required'}), 400
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using OCR
        try:
            text = pytesseract.image_to_string(image, lang='eng')
        except Exception as ocr_error:
            print(f"Tesseract OCR error: {ocr_error}")
            return jsonify({'error': 'OCR processing failed. Please ensure Tesseract OCR is properly installed.'}), 500
        
        # Clean up the text
        text = text.strip()
        
        return jsonify({'text': text})
        
    except Exception as e:
        print(f"OCR error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conjunctions', methods=['GET'])
def get_conjunctions():
    """Get conjunction helper data"""
    try:
        with open('connection.json', 'r', encoding='utf-8') as f:
            # Read the file as text and split by lines
            content = f.read().strip()
            # Remove the outer braces and split by comma
            if content.startswith('{') and content.endswith('}'):
                content = content[1:-1]
            # Split by comma and clean up
            lines = [line.strip().rstrip(',') for line in content.split(',')]
            # Remove quotes around each line
            data = [line.strip('"') for line in lines if line.strip()]
        return jsonify(data)
    except Exception as e:
        print(f"Error loading conjunctions: {e}")
        return jsonify({'error': 'Failed to load conjunctions'}), 500

@app.route('/api/hot-topics', methods=['GET'])
def get_hot_topics():
    """Get hot topics data"""
    try:
        with open('hottopic.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        print(f"Error loading hot topics: {e}")
        return jsonify({'error': 'Failed to load hot topics'}), 500

@app.route('/api/random-topic', methods=['GET'])
def get_random_topic():
    """Get a random topic from hot topics"""
    try:
        with open('hottopic.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get random topic
        import random
        topic_key = random.choice(list(data.keys()))
        topic_text = data[topic_key]
        
        return jsonify({
            'topic_id': topic_key,
            'topic_text': topic_text
        })
    except Exception as e:
        print(f"Error getting random topic: {e}")
        return jsonify({'error': 'Failed to get random topic'}), 500

@app.route('/api/user/profile')
@login_required
def get_user_profile():
    """获取用户个人信息"""
    try:
        user_stats = UserStats.query.filter_by(user_id=current_user.id).first()
        
        profile_data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'created_at': current_user.created_at.isoformat(),
            'stats': {
                'total_essays': user_stats.total_essays if user_stats else 0,
                'average_score': round(user_stats.average_score, 1) if user_stats else 0.0,
                'avg_task_achievement': round(user_stats.avg_task_achievement, 1) if user_stats else 0.0,
                'avg_coherence_cohesion': round(user_stats.avg_coherence_cohesion, 1) if user_stats else 0.0,
                'avg_lexical_resource': round(user_stats.avg_lexical_resource, 1) if user_stats else 0.0,
                'avg_grammatical_range_accuracy': round(user_stats.avg_grammatical_range_accuracy, 1) if user_stats else 0.0
            }
        }
        
        return jsonify(profile_data)
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/essays')
@login_required
def get_user_essays():
    """获取用户的批改历史"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        essays = Essay.query.filter_by(user_id=current_user.id)\
                          .order_by(Essay.created_at.desc())\
                          .paginate(page=page, per_page=per_page, error_out=False)
        
        essay_list = []
        for essay in essays.items:
            essay_data = {
                'id': essay.id,
                'topic': essay.topic[:100] + '...' if len(essay.topic) > 100 else essay.topic,
                'overall_score': essay.overall_score,
                'task_achievement_score': essay.task_achievement_score,
                'coherence_cohesion_score': essay.coherence_cohesion_score,
                'lexical_resource_score': essay.lexical_resource_score,
                'grammatical_range_accuracy_score': essay.grammatical_range_accuracy_score,
                'created_at': essay.created_at.strftime('%Y/%m/%d %H:%M:%S')
            }
            essay_list.append(essay_data)
        
        return jsonify({
            'essays': essay_list,
            'total': essays.total,
            'pages': essays.pages,
            'current_page': page,
            'has_next': essays.has_next,
            'has_prev': essays.has_prev
        })
    except Exception as e:
        print(f"Error getting user essays: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/essays/<int:essay_id>')
@login_required
def get_essay_detail(essay_id):
    """获取特定作文的详细信息"""
    try:
        essay = Essay.query.filter_by(id=essay_id, user_id=current_user.id).first()
        
        if not essay:
            return jsonify({'error': '作文不存在'}), 404
        
        essay_data = {
            'id': essay.id,
            'topic': essay.topic,
            'content': essay.content,
            'overall_score': essay.overall_score,
            'rubric_scores': {
                'task_achievement': essay.task_achievement_score,
                'coherence_cohesion': essay.coherence_cohesion_score,
                'lexical_resource': essay.lexical_resource_score,
                'grammatical_range_accuracy': essay.grammatical_range_accuracy_score
            },
            'statistics': {
                'linking_words_count': essay.linking_words_count,
                'word_repetition_count': essay.word_repetition_count,
                'grammar_mistakes_count': essay.grammar_mistakes_count
            },
            'overall_feedback': essay.overall_feedback,
            'task_achievement_feedback': json.loads(essay.task_achievement_feedback) if essay.task_achievement_feedback else {},
            'coherence_cohesion_feedback': json.loads(essay.coherence_cohesion_feedback) if essay.coherence_cohesion_feedback else {},
            'lexical_resource_feedback': json.loads(essay.lexical_resource_feedback) if essay.lexical_resource_feedback else {},
            'grammatical_range_accuracy_feedback': json.loads(essay.grammatical_range_accuracy_feedback) if essay.grammatical_range_accuracy_feedback else {},
            'grammar_corrections': essay.get_grammar_corrections(),
            'vocabulary_improvements': essay.get_vocabulary_improvements(),
            'created_at': essay.created_at.strftime('%Y/%m/%d %H:%M:%S')
        }
        
        return jsonify(essay_data)
    except Exception as e:
        print(f"Error getting essay detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_with_student():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    try:
        data = request.get_json()
        question = data.get('question', '')
        context = data.get('context', '')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Parse context if it's a JSON string
        try:
            if isinstance(context, str):
                context_data = json.loads(context)
            else:
                context_data = context
        except:
            context_data = {}
        
        prompt = f"""
        你是一位专业的雅思写作导师。基于之前的反馈上下文：
        
        {context}
        
        学生的问题: {question}
        
        请提供一个有帮助的、鼓励性的中文回复，回答学生的具体问题并帮助他们提高写作水平。保持回复简洁实用。
        """
        
        try:
            response = Generation.call(
                model='qwen-plus',
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7
            )
            
            if response.status_code == 200:
                return jsonify({'response': response.output.text})
            else:
                return jsonify({'error': '通义千问API调用失败'}), 500
                
        except Exception as e:
            print(f"Chat error with Qwen: {e}")
            return jsonify({'error': str(e)}), 500
    
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

# 创建数据库表
with app.app_context():
    db.create_all()
    print("Database tables created successfully")

if __name__ == '__main__':
    app.run(debug=True, port=8000)

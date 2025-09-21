from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    essays = db.relationship('Essay', backref='user', lazy=True)
    conversations = db.relationship('Conversation', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Essay(db.Model):
    """作文批改记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # 评分信息
    overall_score = db.Column(db.Float, nullable=False)
    task_achievement_score = db.Column(db.Float, nullable=False)
    coherence_cohesion_score = db.Column(db.Float, nullable=False)
    lexical_resource_score = db.Column(db.Float, nullable=False)
    grammatical_range_accuracy_score = db.Column(db.Float, nullable=False)
    
    # 统计信息
    linking_words_count = db.Column(db.Integer, default=0)
    word_repetition_count = db.Column(db.Integer, default=0)
    grammar_mistakes_count = db.Column(db.Integer, default=0)
    
    # 反馈信息（JSON格式存储）
    overall_feedback = db.Column(db.Text)
    task_achievement_feedback = db.Column(db.Text)
    coherence_cohesion_feedback = db.Column(db.Text)
    lexical_resource_feedback = db.Column(db.Text)
    grammatical_range_accuracy_feedback = db.Column(db.Text)
    
    # 错误纠正（JSON格式存储）
    grammar_corrections = db.Column(db.Text)  # JSON
    vocabulary_improvements = db.Column(db.Text)  # JSON
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_grammar_corrections(self):
        """获取语法纠正信息"""
        if self.grammar_corrections:
            return json.loads(self.grammar_corrections)
        return []
    
    def set_grammar_corrections(self, corrections):
        """设置语法纠正信息"""
        self.grammar_corrections = json.dumps(corrections, ensure_ascii=False)
    
    def get_vocabulary_improvements(self):
        """获取词汇改进信息"""
        if self.vocabulary_improvements:
            return json.loads(self.vocabulary_improvements)
        return []
    
    def set_vocabulary_improvements(self, improvements):
        """设置词汇改进信息"""
        self.vocabulary_improvements = json.dumps(improvements, ensure_ascii=False)
    
    def __repr__(self):
        return f'<Essay {self.id} by User {self.user_id}>'

class Conversation(db.Model):
    """对话记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    essay_id = db.Column(db.Integer, db.ForeignKey('essay.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Conversation {self.id} by User {self.user_id}>'

class UserStats(db.Model):
    """用户统计信息模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # 总体统计
    total_essays = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    
    # 各项平均分
    avg_task_achievement = db.Column(db.Float, default=0.0)
    avg_coherence_cohesion = db.Column(db.Float, default=0.0)
    avg_lexical_resource = db.Column(db.Float, default=0.0)
    avg_grammatical_range_accuracy = db.Column(db.Float, default=0.0)
    
    # 使用统计
    daily_usage_count = db.Column(db.Integer, default=0)
    last_usage_date = db.Column(db.Date)
    
    # 更新时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserStats for User {self.user_id}>'

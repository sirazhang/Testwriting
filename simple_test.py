#!/usr/bin/env python3
"""
简单的系统测试
"""

import requests
import json

def test_system():
    print("🧪 测试雅思作文批改系统...")
    
    # 测试首页
    try:
        response = requests.get('http://127.0.0.1:8000')
        if response.status_code == 200:
            print("✅ 首页加载成功")
        else:
            print(f"❌ 首页加载失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 首页测试失败: {e}")
    
    # 测试作文分析
    test_data = {
        "topic": "Test topic",
        "essay": "This is a test essay to check if the system works properly."
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/analyze',
            headers={'Content-Type': 'application/json'},
            json=test_data
        )
        
        if response.status_code == 200:
            print("✅ 作文分析API正常工作")
            feedback = response.json()
            print(f"   📊 总体评分: {feedback.get('overall_score', 'N/A')}")
        else:
            print(f"❌ 作文分析API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 作文分析测试失败: {e}")
    
    # 测试对话功能
    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/chat',
            headers={'Content-Type': 'application/json'},
            json={
                "question": "测试问题",
                "context": "测试上下文"
            }
        )
        
        if response.status_code == 200:
            print("✅ 对话API正常工作")
            chat_response = response.json()
            print(f"   🤖 AI回复: {chat_response.get('response', 'N/A')[:50]}...")
        else:
            print(f"❌ 对话API失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 对话测试失败: {e}")
    
    print("\n🎉 测试完成！")
    print("💡 请在浏览器中访问 http://127.0.0.1:8000 使用完整功能")

if __name__ == "__main__":
    test_system()

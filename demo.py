#!/usr/bin/env python3
"""
雅思作文批改系统演示脚本
"""

import requests
import json
import time

def test_essay_analysis():
    """测试作文分析功能"""
    print("🧪 测试雅思作文分析功能...")
    
    # 测试数据
    test_topic = """In some cultures, children are often told that they can achieve anything if they try hard enough. What are the advantages and disadvantages of giving children this message? Give reasons for your answer and include any relevant examples from your own knowledge or experience. Write at least 250 words."""
    
    test_essay = """In the social point of view, telling this to children is very important because we are motivating the child not to give up. We are making him to try hard, to make an effort, to read between lines and at the end of that long path achieve their objectives. However, sometimes we face situations where despite our best efforts, we don't achieve what we wanted. For example, when we apply for a job and we don't get it, it was just because another person deserve it more than us.

In the economic point of view, if our objectives demand a lot of money, we are again in the same situation, although we work hard, it would be difficult to achieve it. And at the end, if you have done all these things but you still did not achieve your goal, you will be happy anyway because you did your best.

To sum up, we are teaching to children that they can achieve anything if they try hard enough. This message has both advantages and disadvantages, but I believe the advantages outweigh the disadvantages because it motivates children to work hard and never give up on their dreams."""

    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/analyze',
            headers={'Content-Type': 'application/json'},
            json={
                'topic': test_topic,
                'essay': test_essay
            }
        )
        
        if response.status_code == 200:
            feedback = response.json()
            print("✅ 作文分析成功！")
            print(f"📊 总体评分: {feedback['overall_score']}")
            print(f"📝 总体反馈: {feedback['overall_feedback']}")
            
            print("\n📋 详细反馈:")
            print(f"  - 写作任务回应情况: {feedback['task_response']['score']}")
            print(f"  - 连贯与衔接: {feedback['coherence_cohesion']['score']}")
            print(f"  - 词汇丰富程度: {feedback['lexical_resource']['score']}")
            print(f"  - 语法准确性: {feedback['grammar_accuracy']['score']}")
            
            print(f"\n🔍 语法错误批注数量: {len(feedback['grammar_accuracy']['grammar_corrections'])}")
            print(f"📚 词汇改进建议数量: {len(feedback['lexical_resource']['vocabulary_improvements'])}")
            
            return feedback
        else:
            print(f"❌ 分析失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 请求错误: {e}")
        return None

def test_chat_functionality(feedback_context):
    """测试对话功能"""
    print("\n🤖 测试对话功能...")
    
    test_questions = [
        "我的作文在哪些方面需要改进？",
        "如何提高我的词汇使用？",
        "我的语法错误主要有哪些类型？"
    ]
    
    for question in test_questions:
        print(f"\n👤 问题: {question}")
        
        try:
            response = requests.post(
                'http://127.0.0.1:5000/api/chat',
                headers={'Content-Type': 'application/json'},
                json={
                    'question': question,
                    'context': json.dumps(feedback_context)
                }
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                print(f"🤖 回答: {chat_response['response'][:200]}...")
            else:
                print(f"❌ 对话失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求错误: {e}")
        
        time.sleep(1)  # 避免请求过快

def main():
    """主函数"""
    print("🎓 雅思作文批改系统演示")
    print("=" * 50)
    
    # 测试作文分析
    feedback = test_essay_analysis()
    
    if feedback:
        # 测试对话功能
        test_chat_functionality(feedback)
    
    print("\n" + "=" * 50)
    print("🎉 演示完成！")
    print("💡 您可以在浏览器中访问 http://127.0.0.1:5000 使用完整功能")

if __name__ == "__main__":
    main()

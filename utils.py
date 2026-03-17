from models import Achievement, UserAchievement, Badge, UserBadge, db,Notification
from flask import current_app
import json
import requests
from config import Config

def award_achievement(user, achievement_name):
    achievement = Achievement.query.filter_by(name=achievement_name).first()
    if not achievement:
        return
    if UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first():
        return
    ua = UserAchievement(user_id=user.id, achievement_id=achievement.id)
    user.add_exp(achievement.exp)
    db.session.add(ua)
    # 发送通知
    msg = f"恭喜你获得成就：{achievement.name}！"
    db.session.add(Notification(user_id=user.id, message=msg))
    db.session.commit()

def award_badge(user, badge_name):
    badge = Badge.query.filter_by(name=badge_name).first()
    if not badge:
        return
    if UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
        return
    ub = UserBadge(user_id=user.id, badge_id=badge.id)
    db.session.add(ub)
    # 发送通知
    msg = f"恭喜你获得勋章：{badge.name}！"
    db.session.add(Notification(user_id=user.id, message=msg))
    db.session.commit()

def check_and_award_achievements(user):
    # 首次发帖：动态数+食谱数
    total_posts = user.posts.count() + len(user.recipes)
    if total_posts == 1:
        award_achievement(user, '首次发帖')
    # 示例：评论达人
    if user.comments.count() >= 10:
        award_achievement(user, '评论达人')
    # ...可扩展更多条件

def generate_qwen_stream(prompt):
    """使用 requests 替代 openai 库，调用兼容 API 并以流式返回"""
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {current_app.config.get('DASHSCOPE_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """你是一个专业的厨师和食谱推荐助手。
    请根据用户的需求推荐菜谱，包括菜名、所需食材和简单的制作步骤。
    如果用户询问与烹饪无关的问题，请委婉地引导回美食话题。
    尽量保持回答简洁清晰，使用 Markdown 格式排版。"""
    
    data = {
        "model": "qwen3-max-2026-01-23", # 或替换为您实际使用的模型
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": True # 开启流式输出
    }
    
    try:
        # 使用 requests 发送带有 stream=True 的请求
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                # OpenAI / Qwen 兼容模式的流式数据以 'data: ' 开头
                if decoded_line.startswith('data: ') and decoded_line != 'data: [DONE]':
                    try:
                        chunk = json.loads(decoded_line[6:]) # 去掉前缀 'data: '
                        delta_content = chunk['choices'][0]['delta'].get('content', '')
                        if delta_content:
                            yield f"data: {json.dumps({'type': 'content', 'content': delta_content})}\n\n"
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

def call_dashscope_api(prompt):
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {Config.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-turbo", # 这里写您使用的模型，如 qwen-plus
        "input": {
            "prompt": prompt
        },
        "parameters": {}
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['output']['text']
    else:
        return f"Error: {response.text}"

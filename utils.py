from models import Achievement, UserAchievement, Badge, UserBadge, db,Notification
from openai import OpenAI
from flask import current_app
import json

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
    """调用 Qwen3 API 并以流式返回思考过程和最终结果"""
    client = OpenAI(
        api_key=current_app.config.get('DASHSCOPE_API_KEY'),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    system_prompt = """你是一个专业的厨师和食谱推荐助手。
    请根据用户的需求推荐菜谱，包括菜名、所需食材和简单的制作步骤。
    如果用户询问与烹饪无关的问题，请委婉地引导回美食话题。
    尽量保持回答简洁清晰，使用 Markdown 格式排版。"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    try:
        completion = client.chat.completions.create(
            model="qwen3-max-2026-01-23",
            messages=messages,
            stream=True
        )
        
        for chunk in completion:
            delta = chunk.choices[0].delta
            
                
            #处理最终回复 (content)
            if hasattr(delta, "content") and delta.content:
                yield f"data: {json.dumps({'type': 'content', 'content': delta.content})}\n\n"
                
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

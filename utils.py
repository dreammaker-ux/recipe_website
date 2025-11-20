from models import Achievement, UserAchievement, Badge, UserBadge, db,Notification

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

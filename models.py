from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from db import db

# 多对多中间表
recipe_category = db.Table(
    'recipe_category',
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

class PostComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='post_comments')

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(256))
    user = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))
    likes = db.relationship('PostLike', backref='post', lazy='dynamic')
    comments = db.relationship('PostComment', backref='post', lazy='dynamic')

    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class CookRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    content = db.Column(db.Text)
    image_url = db.Column(db.String(256))
    rating = db.Column(db.Integer)  # 1-5分
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipe = db.relationship('Recipe', backref='cook_records')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_url = db.Column(db.String(256))
    recipes = db.relationship('Recipe', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    cook_records = db.relationship('CookRecord', backref='user', lazy='dynamic')
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)
    achievements = db.relationship('UserAchievement', backref='user', lazy='dynamic')
    badges = db.relationship('UserBadge', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def add_exp(self, amount):
        if self.exp is None:
            self.exp = 0
        self.exp += amount
        # 假设每100经验升一级
        new_level = self.exp // 100 + 1
        if new_level > self.level:
            self.level = new_level

 
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    followed = db.relationship(
        'Follow',
        foreign_keys=[Follow.follower_id],
        backref='follower',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    followers = db.relationship(
        'Follow',
        foreign_keys=[Follow.followed_id],
        backref='followed',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower_id=self.id, followed_id=user.id)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None
    @property
    def unread_notifications_count(self):
        # 只统计未读通知
        return self.notifications.filter_by(is_read=False).count()



class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    cooking_time = db.Column(db.Integer)  # 分钟
    difficulty = db.Column(db.String(20))  # 简单、中等、困难
    servings = db.Column(db.Integer)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    comments = db.relationship('Comment', backref='recipe', lazy=True)
    favorites = db.relationship('Favorite', backref='recipe', lazy=True)
    # 关键：多对多关系
    categories = db.relationship('Category', secondary=recipe_category, backref='recipes')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-5星评分
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    icon = db.Column(db.String(128))  # 图标路径
    exp = db.Column(db.Integer, default=0)  # 获得该成就奖励的经验

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'))
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)
    achievement = db.relationship('Achievement')

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    icon = db.Column(db.String(128))  # 图标路径

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'))
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)
    badge = db.relationship('Badge')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(256), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(32), default='general')
    sender_id = db.Column(db.Integer)
    sender_username = db.Column(db.String(64))




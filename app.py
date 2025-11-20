from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms import LoginForm, RegistrationForm, RecipeForm, CommentForm, ProfileForm, CookRecordForm, PostForm
from config import Config
import random
import os
from sqlalchemy import func
from werkzeug.utils import secure_filename
from itertools import chain
from math import ceil
from db import db
from utils import award_badge, check_and_award_achievements


ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg'}
app = Flask(__name__)
app.config.from_object(Config)

# 1. 初始化扩展
db.init_app(app)
from flask_migrate import Migrate
migrate = Migrate(app, db)

# 2. 现在再导入模型（不要再导入 db）
from models import User, Recipe, Category, Comment, Favorite, CookRecord, Message, Post,PostLike,PostComment,UserBadge,Badge,UserAchievement,Achievement,Notification

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# 初始化成就
achievements = [
    Achievement(name='首次发帖', description='发布第一条动态', icon='first_post.png', exp=10),
    Achievement(name='评论达人', description='累计评论10次', icon='comment_master.png', exp=20),
    # ...更多成就
]
# 初始化勋章
badges = [
    Badge(name='新手厨师', description='注册即获得', icon='newbie.png'),
    Badge(name='活跃用户', description='连续登录7天', icon='active.png'),
    # ...更多勋章
]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 创建数据库表
with app.app_context():
    db.create_all()

with app.app_context():
    if Category.query.count() == 0:
        db.session.add_all([
            Category(name='家常菜'),
            Category(name='川菜'),
            Category(name='粤菜'),
            Category(name='湘菜'),
            Category(name='烘焙'),
            Category(name='素食'),
            Category(name='汤羹'),
            Category(name='小吃'),
            Category(name='甜品'),
            Category(name='西餐'),
            Category(name='饮品')
        ])
        db.session.commit()
        print("已初始化分类数据")
    if Achievement.query.count() == 0:
        db.session.add_all([
            Achievement(name='首次发帖', description='发布第一条动态', icon='first_post.png', exp=10),
            Achievement(name='评论达人', description='累计评论10次', icon='comment_master.png', exp=20),
            # ...更多成就
        ])
        db.session.commit()
    if Badge.query.count() == 0:
        db.session.add_all([
            Badge(name='新手厨师', description='注册即获得', icon='newbie.png'),
            Badge(name='活跃用户', description='连续登录7天', icon='active.png'),
            # ...更多勋章
        ])
        db.session.commit()

# 路由
@app.route('/')
def index():
    # 获取最新的食谱
    latest_recipes = Recipe.query.order_by(Recipe.created_at.desc()).limit(6).all()
    return render_template('index.html', latest_recipes=latest_recipes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # 检查用户名和邮箱是否已存在
        existing_user = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()
        
        if existing_user:
            flash('用户名已存在，请选择其他用户名', 'danger')
            return render_template('register.html', form=form)
        
        if existing_email:
            flash('邮箱已被注册，请使用其他邮箱', 'danger')
            return render_template('register.html', form=form)
        
        # 创建新用户
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # 注册即授予新手勋章
        award_badge(user, '新手厨师')
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('index'))

@app.route('/recipes')
def recipes():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search_query = request.args.get('q', '')

    query = Recipe.query

    if category_id:
        query = query.join(Recipe.categories).filter(Category.id == category_id)

    if search_query:
        query = query.filter(Recipe.title.contains(search_query) | Recipe.description.contains(search_query))

    recipes = query.order_by(Recipe.created_at.desc()).paginate(
        page=page, per_page=9, error_out=False
    )

    categories = Category.query.all()

    return render_template('recipes.html', recipes=recipes, categories=categories,
                          category_id=category_id, search_query=search_query)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = CommentForm()
    
    # 计算平均评分
    if recipe.comments:
        avg_rating = sum(comment.rating for comment in recipe.comments) / len(recipe.comments)
    else:
        avg_rating = 0

    tips = [
        "用柠檬汁可以防止苹果变色哦！",
        "炒菜时先热锅再加油，食材更不易粘锅。",
        "腌制肉类时加点糖，口感更嫩滑。",
        "剩饭做炒饭更有颗粒感。",
        "煮面条时加点盐，面条更筋道。"
    ]
    creative_tip = random.choice(tips)
    hot_recipes = (
        db.session.query(Recipe)
        .outerjoin(Favorite, Recipe.id == Favorite.recipe_id)
        .group_by(Recipe.id)
        .order_by(func.count(Favorite.id).desc())
        .limit(5)
        .all()
    )
    return render_template('recipe_detail.html', recipe=recipe,hot_recipes=hot_recipes, creative_tip=creative_tip, form=form, avg_rating=avg_rating)

@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    # 设置分类下拉选项
    form.categories.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        # 处理图片上传
        image_url = None
        if hasattr(form, 'image') and form.image.data:
            filename = secure_filename(form.image.data.filename)
            upload_dir = os.path.join('static', 'recipe_images')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            file_path = os.path.join(upload_dir, filename)
            form.image.data.save(file_path)
            image_url = '/' + file_path.replace('\\', '/')
        else:
            # 兼容填写图片链接的情况
            image_url = form.image_url.data or None

        # 创建食谱对象
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            cooking_time=form.cooking_time.data,
            difficulty=form.difficulty.data,
            servings=form.servings.data,
            image_url=image_url,
            user_id=current_user.id
        )

        # 分类处理
        category_ids = [int(cid) for cid in (form.categories.data or [])]
        if category_ids:
            recipe.categories = Category.query.filter(Category.id.in_(category_ids)).all()
        else:
            recipe.categories = []

        db.session.add(recipe)
        current_user.add_exp(20)  # 例如发食谱+20经验
        db.session.commit()
        check_and_award_achievements(current_user)
        flash('食谱发布成功！', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))

    return render_template('add_recipe.html', form=form)

@app.route('/recipe/<int:recipe_id>/comment', methods=['POST'])
@login_required
def add_comment(recipe_id):
    form = CommentForm()
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            rating=form.rating.data,
            user_id=current_user.id,
            recipe_id=recipe_id
        )
        
        db.session.add(comment)
        current_user.add_exp(2)  # 例如评论+2经验
        db.session.commit()
        check_and_award_achievements(current_user)
        flash('评论发布成功！', 'success')
    
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/favorite/<int:recipe_id>', methods=['POST'])
@login_required
def toggle_favorite(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash('已取消收藏', 'info')
    else:
        favorite = Favorite(user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(favorite)
        db.session.commit()
        flash('已添加到收藏', 'success')
    
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('不能关注自己', 'warning')
    elif not current_user.is_following(user):
        current_user.follow(user)
        db.session.commit()
        flash(f'已关注 {user.username}', 'success')
    else:
        flash('已关注该用户', 'info')
    return redirect(request.referrer or url_for('profile'))

@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('不能取消关注自己', 'warning')
    elif current_user.is_following(user):
        current_user.unfollow(user)
        db.session.commit()
        flash(f'已取消关注 {user.username}', 'info')
    else:
        flash('未关注该用户', 'info')
    return redirect(request.referrer or url_for('profile'))

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    # 只允许作者本人删除
    if recipe.user_id != current_user.id:
        flash('您没有权限删除该食谱', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    db.session.delete(recipe)
    db.session.commit()
    flash('食谱已删除', 'success')
    return redirect(url_for('recipes'))

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != current_user.id:
        flash('您没有权限编辑该食谱', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    form = RecipeForm(obj=recipe)
    form.categories.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.description = form.description.data
        recipe.ingredients = form.ingredients.data
        recipe.instructions = form.instructions.data
        recipe.cooking_time = form.cooking_time.data
        recipe.difficulty = form.difficulty.data
        recipe.servings = form.servings.data
        recipe.image_url = form.image_url.data

        category_ids = [int(cid) for cid in (form.categories.data or [])]
        if category_ids:
            recipe.categories = Category.query.filter(Category.id.in_(category_ids)).all()
        else:
            recipe.categories = []

        db.session.commit()
        flash('食谱已更新', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))

    return render_template('add_recipe.html', form=form, edit=True)

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    can_edit = (current_user.id == user.id)
    form = ProfileForm(obj=user) if can_edit else None

    # 获取该用户发布的食谱
    user_recipes = Recipe.query.filter_by(user_id=user.id).all()
    # 获取该用户收藏的食谱
    favorite_recipes = [fav.recipe for fav in user.favorites]
    # 获取打卡记录
    cook_records = user.cook_records.order_by(CookRecord.created_at.desc()).all()
    # 获取评论
    comments = user.comments.order_by(Comment.created_at.desc()).all()
    notifications = []
    if can_edit:
        notifications = user.notifications.order_by(Notification.created_at.desc()).limit(10).all()

    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # 获取该用户发布的动态
    posts = user.posts.order_by(Post.timestamp.desc()).all()

    # 合并动态
    activities = list(chain(
        [{'type': 'recipe', 'obj': r, 'created_at': r.created_at} for r in user_recipes],
        [{'type': 'cook_record', 'obj': c, 'created_at': c.created_at} for c in cook_records],
        [{'type': 'comment', 'obj': cm, 'created_at': cm.created_at} for cm in comments],
        [{'type': 'post', 'obj': p, 'created_at': p.timestamp} for p in posts]
    ))
    activities.sort(key=lambda x: x['created_at'], reverse=True)


    # 动态分页
    total = len(activities)
    pages = ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    activities_page = activities[start:end]

    pagination = {
        'page': page,
        'pages': pages,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_num': page - 1,
        'next_num': page + 1,
        'iter_pages': range(1, pages + 1)
    }

    if can_edit and form and form.validate_on_submit():
        user.username = form.username.data
        if form.avatar.data:
            filename = secure_filename(form.avatar.data.filename)
            upload_dir = os.path.join('static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            avatar_path = os.path.join(upload_dir, filename)
            form.avatar.data.save(avatar_path)
            user.avatar_url = '/' + avatar_path.replace('\\', '/')
        db.session.commit()
        flash('资料已更新', 'success')
        return redirect(url_for('profile', user_id=user.id))

    return render_template(
        'profile.html',
        form=form,
        user=user,
        can_edit=can_edit,
        user_recipes=user_recipes,
        favorite_recipes=favorite_recipes,
        activities=activities_page,
        activities_pagination=pagination,
        PostComment=PostComment,
        notifications=notifications,
        unread_notifications_count=user.unread_notifications_count,
        UserBadge=UserBadge,
        UserAchievement=UserAchievement
    )

@app.route('/profile/<int:user_id>/followers')
@login_required
def followers_list(user_id):
    user = User.query.get_or_404(user_id)
    # 取出所有粉丝用户
    followers = [f.follower for f in user.followers]
    return render_template('user_list.html', user=user, users=followers, list_type='followers')

@app.route('/profile/<int:user_id>/following')
@login_required
def following_list(user_id):
    user = User.query.get_or_404(user_id)
    # 取出所有被关注的用户
    following = [f.followed for f in user.followed]
    return render_template('user_list.html', user=user, users=following, list_type='following')

@app.route('/hot_recipes')
def hot_recipes():
    category_id = request.args.get('category', type=int)
    categories = Category.query.all()
    current_category = None
    query = db.session.query(Recipe).outerjoin(Favorite, Recipe.id == Favorite.recipe_id)
    if category_id:
        query = query.join(Recipe.categories).filter(Category.id == category_id)
        current_category = Category.query.get(category_id)
    hot_recipes = (
        query.group_by(Recipe.id)
        .order_by(func.count(Favorite.id).desc())
        .limit(20)
        .all()
    )
    return render_template(
        'hot_recipes.html',
        hot_recipes=hot_recipes,
        categories=categories,
        category_id=category_id,
        current_category=current_category
    )


def allowed_audio(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

@app.route('/recipe/<int:recipe_id>/cook', methods=['GET', 'POST'])
def cook_mode(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = CookRecordForm()
    music_url = url_for('static', filename='music/cook1.mp3')
    if request.method == 'POST' and 'audio_file' in request.files:
        file = request.files['audio_file']
        if file and allowed_audio(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('static', 'music')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            music_url = '/' + file_path.replace('\\', '/')
            flash('音频上传成功！', 'success')
        else:
            flash('仅支持mp3/wav/ogg格式音频', 'danger')
    if form.validate_on_submit():
        image_url = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            upload_dir = os.path.join('static', 'cook_records')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            file_path = os.path.join(upload_dir, filename)
            form.image.data.save(file_path)
            image_url = '/' + file_path.replace('\\', '/')
        record = CookRecord(
            user_id=current_user.id,
            recipe_id=recipe.id,
            content=form.content.data,
            rating=form.rating.data,
            image_url=image_url
        )
        db.session.add(record)
        db.session.commit()
        flash('打卡成功，已上传到社区！', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    return render_template('cook_mode.html', recipe=recipe, music_url=music_url, form=form)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form.get('receiver_id', type=int)
    content = request.form.get('content', type=str)
    if not receiver_id or not content:
        return jsonify({'status': 'fail', 'msg': '内容不能为空'}), 400
    msg = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
   # 新增：写入通知，增加type字段
    notify = Notification(
        user_id=receiver_id,
        message=f"{current_user.username} 给你发来新消息",
        type='friend_message',  # 指定类型
        sender_id=current_user.id,
        sender_username=current_user.username
    )
    db.session.add(notify)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/get_messages/<int:user_id>')
@login_required
def get_messages(user_id):
    # 获取与 user_id 的所有消息
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    # 标记对方发来的未读消息为已读
    for m in messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()
    return jsonify([
        {
            'sender_id': m.sender_id,
            'receiver_id': m.receiver_id,
            'content': m.content,
            'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for m in messages
    ])

@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        image_url = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            image_path = os.path.join('static', 'uploads', filename)
            form.image.data.save(image_path)
            image_url = '/' + image_path  # 用于模板显示
        post = Post(content=form.content.data, user_id=current_user.id, image_url=image_url)
        db.session.add(post)
        current_user.add_exp(10)# 例如发动态+10经验
        db.session.commit()
        check_and_award_achievements(current_user)
        flash('动态已发表！')
        return redirect(url_for('profile', user_id=current_user.id))
    return render_template('add_post.html', form=form)

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash('无权编辑该动态', 'danger')
        return redirect(url_for('profile', user_id=current_user.id))
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.content = form.content.data
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            image_path = os.path.join('static', 'uploads', filename)
            form.image.data.save(image_path)
            post.image_url = '/' + image_path
        db.session.commit()
        flash('动态已更新！', 'success')
        return redirect(url_for('profile', user_id=current_user.id))
    return render_template('add_post.html', form=form, edit=True)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash('无权删除该动态', 'danger')
        return redirect(url_for('profile', user_id=current_user.id))
    db.session.delete(post)
    db.session.commit()
    flash('动态已删除！', 'success')
    return redirect(url_for('profile', user_id=current_user.id))

@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if not existing:
        like = PostLike(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
    return redirect(request.referrer or url_for('profile', user_id=post.user_id))

@app.route('/post/<int:post_id>/unlike', methods=['POST'])
@login_required
def unlike_post(post_id):
    like = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
    return redirect(request.referrer or url_for('profile', user_id=current_user.id))

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_post(post_id):
    content = request.form.get('content', '').strip()
    if not content:
        flash('评论内容不能为空', 'danger')
        return redirect(request.referrer or url_for('profile', user_id=current_user.id))
    comment = PostComment(post_id=post_id, user_id=current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    flash('评论成功', 'success')
    return redirect(request.referrer or url_for('profile', user_id=current_user.id))

@app.route('/notification/<int:notification_id>/read', methods=['POST'])
@login_required
def read_notification(notification_id):
    n = Notification.query.get_or_404(notification_id)
    if n.user_id == current_user.id:
        n.is_read = True
        db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok'})
    return redirect(url_for('profile', user_id=current_user.id))


@app.context_processor
def inject_first_unread_notification():
    if current_user.is_authenticated:
        first_unread = current_user.notifications.filter_by(is_read=False).order_by(Notification.created_at.desc()).first()
        return dict(first_unread_notification=first_unread)
    return dict(first_unread_notification=None)

if __name__ == '__main__':
    app.run(debug=True)

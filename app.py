from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Recipe, Category, Comment, Favorite
from forms import LoginForm, RegistrationForm, RecipeForm, CommentForm
from config import Config
   
app = Flask(__name__)
app.config.from_object(Config)

# 初始化扩展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
    
    return render_template('recipe_detail.html', recipe=recipe, form=form, avg_rating=avg_rating)

@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    form.categories.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            cooking_time=form.cooking_time.data,
            difficulty=form.difficulty.data,
            servings=form.servings.data,
            image_url=form.image_url.data or None,
            user_id=current_user.id
        )

        category_ids = [int(cid) for cid in (form.categories.data or [])]
        if category_ids:
            recipe.categories = Category.query.filter(Category.id.in_(category_ids)).all()
        else:
            recipe.categories = []
        db.session.add(recipe)
        db.session.commit()
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
        db.session.commit()
        
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

@app.route('/profile')
@login_required
def profile():
    user_recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    favorite_recipes = [fav.recipe for fav in current_user.favorites]
    
    return render_template('profile.html', user_recipes=user_recipes, favorite_recipes=favorite_recipes)

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

if __name__ == '__main__':
    app.run(debug=True)

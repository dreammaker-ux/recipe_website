from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from wtforms import SelectMultipleField
   
class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

class RecipeForm(FlaskForm):
    title = StringField('食谱标题', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('食谱描述')
    ingredients = TextAreaField('食材', validators=[DataRequired()])
    instructions = TextAreaField('步骤', validators=[DataRequired()])
    cooking_time = IntegerField('烹饪时间(分钟)', validators=[DataRequired(), NumberRange(min=1)])
    difficulty = SelectField('难度', choices=[('简单', '简单'), ('中等', '中等'), ('困难', '困难')])
    servings = IntegerField('份量', validators=[DataRequired(), NumberRange(min=1)])
    image_url = StringField('图片URL')
    submit = SubmitField('发布食谱')
    categories = SelectMultipleField('分类', coerce=int)

class CommentForm(FlaskForm):
    content = TextAreaField('评论', validators=[DataRequired()])
    rating = SelectField('评分', choices=[(5, '5星'), (4, '4星'), (3, '3星'), (2, '2星'), (1, '1星')])
    submit = SubmitField('提交评论')
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, FileField, SelectField, SubmitField,TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from wtforms import SelectMultipleField
from flask_wtf.file import FileField, FileAllowed

class PostForm(FlaskForm):
    content = TextAreaField('内容', validators=[DataRequired(), Length(max=500)])
    image = FileField('图片', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '仅支持图片格式')])
    submit = SubmitField('发表')

class CookRecordForm(FlaskForm):
    content = TextAreaField('我的评价/心得', validators=[DataRequired()])
    rating = SelectField('评分', choices=[(5, '5星'), (4, '4星'), (3, '3星'), (2, '2星'), (1, '1星')], coerce=int)
    image = FileField('上传图片', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '仅支持图片文件')])
    submit = SubmitField('打卡并上传')

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    avatar_url = StringField('头像URL')
    submit = SubmitField('注册')

class RecipeForm(FlaskForm):
    title = StringField('食谱标题', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('食谱描述')
    ingredients = TextAreaField('食材', validators=[DataRequired()])
    instructions = TextAreaField('步骤', validators=[DataRequired()])
    cooking_time = IntegerField('烹饪时间(分钟)', validators=[DataRequired(), NumberRange(min=1)])
    difficulty = SelectField('难度', choices=[('简单', '简单'), ('中等', '中等'), ('困难', '困难')])
    servings = IntegerField('份量', validators=[DataRequired(), NumberRange(min=1)])
    image = FileField('上传图片', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '仅支持图片文件')])
    image_url = StringField('图片链接')
    submit = SubmitField('发布食谱')
    categories = SelectMultipleField('分类', coerce=int)

class MessageForm(FlaskForm):
    content = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('发送')

class CommentForm(FlaskForm):
    content = TextAreaField('评论', validators=[DataRequired()])
    rating = SelectField('评分', choices=[(5, '5星'), (4, '4星'), (3, '3星'), (2, '2星'), (1, '1星')])
    submit = SubmitField('提交评论')

class ProfileForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    avatar = FileField('上传头像', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '仅支持图片文件')])
    submit = SubmitField('保存')
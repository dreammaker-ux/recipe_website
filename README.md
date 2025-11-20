# 食光慢煮（recipe_website）

一个基于 Flask和MySql 的美食社区网站，支持用户注册、登录、发布和收藏食谱、动态、评论、私信聊天、成就勋章等功能。
<img width="2329" height="3209" alt="image" src="https://github.com/user-attachments/assets/38f0b0bc-ddaf-4e7e-9126-1c632ba28a2c" />

## 项目地址

[https://github.com/dreammaker-ux/recipe_website.git](https://github.com/dreammaker-ux/recipe_website.git)

## 环境要求

- Python 3.8 及以上 4.2 及以下
- pip
- 推荐使用虚拟环境（venv）

## 安装与运行

1. **克隆项目代码**

git clone https://github.com/dreammaker-ux/recipe_website.git cd recipe_website


2. **创建并激活虚拟环境**

python -m venv venv

Windows
venv\Scripts\activate

macOS/Linux
source venv/bin/activate


3. **安装依赖**

pip install -r requirements.txt
   

4. **初始化数据库**

   - 首次运行会自动创建数据库和表：

   python app.py

   - 或使用 Flask-Migrate 进行迁移（可选）：

   flask db init
   flask db migrate
   flask db upgrade


5. **运行项目**

   python app.py
     

默认访问地址：[http://127.0.0.1:5000](http://127.0.0.1:5000)

## 主要功能

- 用户注册、登录、登出
- 个人资料编辑、头像上传
- 发布/收藏/评论食谱
- 发布/评论/点赞动态
- 私信聊天
- 成就与勋章系统
- 消息通知
- 食谱分类浏览与搜索

## 目录结构 

recipe_website/
├── app.py                # 主程序入口 
├── models.py             # 数据库模型 
├── forms.py              # 表单定义 
├── utils.py              # 工具函数 
├── db.py                 # 数据库实例 
├── config.py             # 配置文件 
├── requirements.txt      # 依赖列表 
├── static/               # 静态资源（css/img/js等） 
├── templates/            # Jinja2模板 
├── migrations/           # 数据库迁移文件夹 
└── README.md             # 项目说明
   

import pymysql

conn = pymysql.connect(
    host='localhost',
    user='xgy',  # 替换为你的数据库用户名
    password='197111226716',  # 替换为你的数据库密码
    database='recipe_website',
    charset='utf8mb4'
)
cursor = conn.cursor()
cursor.execute("SELECT id, title, image_url FROM recipe")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}, 标题: {row[1]}, 图片链接: {row[2]}")
cursor.close()
conn.close()

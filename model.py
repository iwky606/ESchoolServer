# 数据库设计
# SQLAlchemy的orm模型

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    username= db.Column(db.String(128), primary_key=True, nullable=False)  # 学号 主键
    pwdBuct = db.Column(db.String(128), nullable=True,default="")  # 北化在线密码
    pwdJwxt = db.Column(db.String(128), nullable=True,default="")  # 教务系统密码



from flask import Flask, render_template, session, g, request
from flask_migrate import Migrate
from sqlalchemy.dialects.mysql import insert
import config
from decorators import login_required
from model import db, User
from module.SpiderCourse.SpiderCourse import SpiderCourse
from module.SpiderJWS.SpiderJwxt import SpiderJwxt

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

migrate = Migrate(app, db)


# 首页域名
@app.route('/')
def index():
    return render_template("index.html")


@app.before_request
def BeforeRequest():
    if 'username' in session:
        username=session['username']
        setattr(g,'username',username)
    else:
        setattr(g,'username',None)


# 用户登录到北化在线
@app.route("/login/buct", methods=['POST'])
def loginToBuct():
    user = request.get_json()
    username = user['username']
    pwdBuct = user['password']

    spider = SpiderCourse(username=user['username'], password=user['password'])
    spider.login()

    # 是否登录成功
    if not spider.isLogin:
        return {
            "msg": "登录失败，账号密码错误",
            "status": False
        }
    spider.logout()

    # 添加用户
    # 用户 如果存在，变为修改
    # 如果不存在，则添加用户
    statement = insert(User).values(username=username, pwdBuct=pwdBuct).on_duplicate_key_update(
        pwdBuct=pwdBuct)
    db.session.execute(statement)
    db.session.commit()

    # 添加cookie
    session['username'] = username
    session.permanent = True

    return {
        "msg": "登录成功",
        "status": True
    }


# 用户登录到教务系统
@app.route("/login/jwxt", methods=['POST'])
def loginToJwxt():
    user = request.get_json()
    username = user['username']
    pwdJwxt = user['password']
    spider = SpiderJwxt(username=username, password=pwdJwxt)
    spider.login()

    # 是否登录成功
    if not spider.isLogin:
        return {
            "msg": "登录失败，账号密码错误",
            "status": False
        }

    # 添加用户
    # 用户 如果存在，变为修改
    # 如果不存在，则添加用户
    statement = insert(User).values(username=username, pwdJwxt=pwdJwxt).on_duplicate_key_update(
        pwdJwxt=pwdJwxt)
    db.session.execute(statement)
    db.session.commit()

    # 添加cookie
    session['username'] = username
    session.permanent = True

    return {
        "msg": "登录成功",
        "status": True
    }


# 获取作业信息
@app.route("/getTask")
@login_required
def getTask():
    user = User.query.filter_by(username=g.username).first()  # User
    spider = SpiderCourse(user.username, user.pwdBuct)
    data = spider.getTask_by_reminder()
    return data


# 获取考试信息
@app.route("/getExam")
@login_required
def getExam():
    user = User.query.filter_by(username=g.username).first()
    spider = SpiderJwxt(user.username, user.pwdJwxt)
    print(user.pwdJwxt)
    data = spider.getExam()
    return data


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

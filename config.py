DEBUG=True
ENV="development"
# DEBUG=False
# ENV='production'

# 盐
# 用于session
SECRET_KEY='SECRET_KEY'

# 数据库配置
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{user_name}:{password}@{host}:{port}/{database}".format(
    user_name='root',
    password='password',
    host='ip',
    port=3306,
    database='ESchoolServer'
)

SQLALCHEMY_TRACK_MODIFICATIONS = False




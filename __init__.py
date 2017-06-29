from flask import Flask
from flask_bootstrap import Bootstrap
#from .data_model import init_db,DBSession
from .config import config
from flask_login import LoginManager
from flask_mail import Mail
from flask_pagedown import PageDown


#db = init_db()							   #初始化数据库连接，？？？？？？
login_manager = LoginManager()
mail = Mail()
pagedown = PageDown()

def create_app():
	app = Flask(__name__)
	app.config.from_object(config)		   #导入配置
	from .reg import reg                   #从reg蓝本中导入蓝本实例
	app.register_blueprint(reg, url_prefix='/reg')   #在app中注册蓝本
	from .main import main
	app.register_blueprint(main)
	bootstrap = Bootstrap(app)
	login_manager.init_app(app)
	mail.init_app(app)
	pagedown.init_app(app)
	login_manager.session_protection = 'strong'
	login_manager.login_view = 'reg.load_in'
	return app


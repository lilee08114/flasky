import os


class config():
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'no one could guess!'
	SUBJECT_PREFIX = '主题前缀'
	MAIL_SENDER='发送者<422758783@qq.com>'
	MAIL_SERVER = 'smtp.qq.com'
	MAIL_PASSWORD = 'krzarygxvvhzcafb'
	MAIL_USERNAME = '422758783@qq.com'
	MAIL_USE_SSL = False
	MAIL_USE_TLS = True
	MAIL_PORT = 587
	DEBUG = True
	ADMIN_MAIL='422758783@qq.com'
	SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:a123@localhost:3306/newtesttable'
	def init_app(app):
		pass

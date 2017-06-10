from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app

Base = declarative_base()
engine = create_engine('mysql+mysqlconnector://root:a123@localhost:3306/Flaskr_User_information')
session_factory = sessionmaker(bind = engine)
DBSession = scoped_session(session_factory)

class Table1(UserMixin, Base):

	__tablename__ = 'table1'

	id = Column(Integer, autoincrement = True, primary_key = True)
	username = Column(String(20), unique = True)
	usermail = Column(String(30), unique = True)
	password_hash = Column(String(300))
	confirm = Column(Boolean, default = False)
	

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	@property
	def password(self):
		raise AttributeError('FBI WARNING!')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)
	'''
	为什么会出现表单实例没有绑定session导致写入数据库的行为失败？？
	def change_code(self, new_code):
		db_session = DBSession
		self.password = new_code
		db_session.add(self)
		db_session.commit()
		db_session.close()
	'''

	def generate_confirm_token(self, expiration=600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'confirm':self.id})

	def verify_token(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		if s.loads(token).get('confirm') == self.id:
			db_session = DBSession
			self.confirm = True
			db_session.add(self)
			db_session.commit()
			db_session.close()

			print ('confirm state has been set to True')
			return True
		else:
			return False




@login_manager.user_loader
def load_user(user_id):
	db_session = DBSession
	try:
		return db_session.query(Table1).get(int(user_id))
	except:
		raise
	finally:
		db_session.close()

def init_db():
	#Base.metadata.drop_all(engine)
	Base.metadata.create_all(engine)
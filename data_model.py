from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, 		 				 Boolean, DateTime, Text
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from functools import wraps
from datetime import datetime

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
	role_id = Column(Integer, ForeignKey('roles.id'))
	
	realname = Column(String(0,24))
	gender = Column(String(0,4))
	age = Column(String(0,2))
	location = Column(String(0,64))
	reg_time = Column(Datetime(), default = dateime.utcnow())
	last_time = Column(Datetime(), default = dateime.utcnow())
	introduction = Column(Text(), default = 'this is a lazy budy, and left nothing')
	
	role = relationship('Role', back_populates='user')

	#---------------------------------------------------赋值权限
	def __init__(self, **kwargs):
		super(Table1, self).__init__(**kwargs)

		print ('in the --init-- assign roles')
		if self.role is None:
			db_session=DBSession
			if self.usermail == current_app.config['ADMIN_MAIL']:
				self.role = db_session.query(Role).filter_by(name='owner').first()
			else:
				self.role = db_session.query(Role).filter_by(name='normal').first()
			print ('before commit ,let see what in role')
			print (self.role)
			db_session.close()
			#db_session.commit()
	#---------------------------------------------------权限检查,及装饰器
	def can(self, action):
		db_session = DBSession
		per = db_session.query(Table1).filter_by(username=self.username).first()
		if (action & per.role.permission) == action:
			return True
		return False

	def is_admin(self):
		return self.role.permission == Permission.ADMIN
	
	
	#---------------------------------------------------
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

class Role(UserMixin, Base):
	print ('before role table ')
	__tablename__ = 'roles'
	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String(64), unique=True)
	permission = Column(Integer)
	default = Column(Boolean, default=False)

	user = relationship('Table1', back_populates='role')
	#------------------------------------------------------插入角色
	@staticmethod
	def insert_role():
		print ('in the static method')
		right = {'normal':(Permission.FOLLOW|
							Permission.COMMENT|
							Permission.WRITE, False),
				 'manager':(Permission.COMMENT|
				 			Permission.FOLLOW|
				 			Permission.WRITE|
				 			Permission.SHUTDOWN, True),
				 'owner':(0xff, True)}
		db_session=DBSession
		for i in right:
			temp_role = db_session.query(Role).filter_by(name=i).first()
			if temp_role is None:
				new_role = Role(name=i,
								permission=right.get(i)[0],
								default=right.get(i)[1])
				db_session.add(new_role)
		db_session.commit()
		db_session.close()
	#----------------------------------------------------


class Permission():
	#-----------------------action below-----------------
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE = 0x04
	SHUTDOWN = 0x08
	ADMIN = 0x80

#----------------下面这个类继承自AnonymousUserMixin，他所以具有所有之前未登录用户的特征
#----------------此类的功能就是在原有的anoymoususer基础上添加了can和is_admion功能
#----------------并将anonymous_user指向此类，因为此类继承原有功能和新添加的2个功能
#----------------因此实现了向anonymous添加功能的作用
class AnonymousUser(AnonymousUserMixin):
	def can(self, action):
		return False
	def is_admin(self):
		return False
login_manager.anonymous_user = AnonymousUser
#--------------------------------------------------------------------------------
>>>>>>> eeeb89388303be63a80e4ee558b3d50636c800b5
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
	#print ('in the create all')
	
	Base.metadata.create_all(engine)
	#Role.insert_role()
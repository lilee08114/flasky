from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean, DateTime, Text, event, Table
from sqlalchemy.orm import sessionmaker, relationship, scoped_session,backref
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from functools import wraps
from datetime import datetime
from . import create_app
import bleach
from markdown import markdown


Base = declarative_base()
engine = create_engine('mysql+mysqlconnector://root:a123@localhost:3306/Flaskr_User_information', echo=True)
session_factory = sessionmaker(bind = engine)
DBSession = scoped_session(session_factory)

class Follow(UserMixin, Base):
	__tablename__ = 'follow'

	followed_id = Column(Integer, ForeignKey('table1.id'),primary_key=True)
	follower_id = Column(Integer, ForeignKey('table1.id'),primary_key=True)
	time = Column(DateTime, default=datetime.utcnow())

	
class Table1(UserMixin, Base):
	__tablename__ = 'table1'

	id = Column(Integer, autoincrement = True, primary_key = True)
	username = Column(String(20), unique = True)
	usermail = Column(String(30), unique = True)
	password_hash = Column(String(300))
	confirm = Column(Boolean, default = False)
	role_id = Column(Integer, ForeignKey('roles.id'))
	
	realname = Column(String(24))
	gender = Column(String(8))
	age = Column(String(2))
	location = Column(String(64))
	reg_time = Column(DateTime(), default = datetime.utcnow())
	last_time = Column(DateTime(), default = datetime.utcnow())
	introduction = Column(Text(), default = 'this is a lazy budy, and left nothing')

	followed = relationship('Follow', primaryjoin=(id==Follow.follower_id),
							backref=backref('follower',lazy='joined'), lazy='dynamic')
	
	follower = relationship('Follow', primaryjoin=(id==Follow.followed_id),
							backref=backref('followed',lazy='joined'), lazy='dynamic')

	

	role = relationship('Role', back_populates='user')
	articles = relationship('Post', back_populates='author',lazy='dynamic')
	comment = relationship('Comment', back_populates='author',lazy='dynamic')
	
	#-----------------------------当前用户所关注的人的文章
	def followed_article(self):
		db_session = DBSession
		post_obj = db_session.query(Post).join(Follow, Follow.followed_id==Post.author_id).\
									filter(Follow.follower_id==self.id)
		return post_obj						

	#---------------------------添加虚假信息，便于测试
	@staticmethod
	def insert_message(count):
		import forgery_py
		db_session=DBSession
		from random import randint
		for i in range(count):
			user=Table1(username=forgery_py.internet.user_name(True),
				    usermail=forgery_py.internet.email_address(),
				    password=forgery_py.lorem_ipsum.word() ,
				    confirm=True,
				    realname=forgery_py.name.full_name(),
				    gender=['Man','Woman'][randint(0,1)],
					age=randint(18,80),
					location=forgery_py.address.city(),
					reg_time=forgery_py.date.date(True),
					last_time=forgery_py.date.date(True),
					introduction=forgery_py.lorem_ipsum.sentence())
			db_session.add(user)
			#这里出现了一个问题，因为有__init__语句存在，不能多次添加table对象
			#然后一次性commit，只能挨个add和commit，否则会失败，why？
			try:
				db_session.commit()
			except:
				db_session.rollback()
				raise
			finally:
				print ('aaaaaaaaaaaa')
				db_session.close()
	
	#---------------------------------------------------赋值权限
	def __init__(self, **kwargs):
		super(Table1, self).__init__(**kwargs)
		'''
		此处如果不使用try， 在静态添加虚假测试数据时会因为没有请求，而没有请求
		上下文，也就没有应用上下文（应用上下文的2重方式：1随着请求上下文的出现
		自动出现 2显式的使用app_context声明），所以需要显式声明应用上下文，
		同时和正常情况下有请求时相区分开。
		但，这是一种好的方式吗？
		'''
		if self.role is None:
			db_session=DBSession
			try:
				current_app.config['ADMIN_MAIL']
			except RuntimeError:
				web = create_app()
				with web.app_context():
					if self.usermail == current_app.config['ADMIN_MAIL']:
						self.role = db_session.query(Role).filter_by(name='owner').first()
					else:
						self.role = db_session.query(Role).filter_by(name='normal').first()
			else:
				
				if self.usermail == current_app.config['ADMIN_MAIL']:
						self.role = db_session.query(Role).filter_by(name='owner').first()
				else:
					self.role = db_session.query(Role).filter_by(name='normal').first()
			finally:
				#print (self.role)
				db_session.close()
				#db_session.commit()
	#---------------------------------------------------权限检查,及装饰器
	def can(self, action):
		'''
		这里为什么用self会出错？role也不必去DB查询啊
		'''
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

			return True
		else:
			return False
#----------------------------------关注的人的列表,列表里是user对象

	def followed_list(self):
		l = []
		db_session=DBSession
		user = db_session.query(Table1).filter_by(id=self.id).first()
		for i in user.followed:
			l.append(i.followed)
		return l
		
		
class Comment(UserMixin, Base):
	__tablename__ = 'comments'
	
	id = Column(Integer, primary_key=True, autoincrement=True)
	post_id = Column(Integer, ForeignKey('posts.id'))
	author_id = Column(Integer, ForeignKey('table1.id'))
	he_said = Column(Text())
	time = Column(DateTime(), default=datetime.utcnow())
	
	post = relationship('Post', back_populates = 'comment')
	author = relationship('Table1', back_populates='comment')


class Role(UserMixin, Base):
	
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
		right = {'shut':(0x00,False),
				 'normal':(Permission.FOLLOW|
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

class Post(UserMixin, Base):

	__tablename__ = 'posts'
	id = Column(Integer, primary_key=True, autoincrement=True)
	article = Column(Text())
	article_html = Column(Text())
	post_time = Column(DateTime(), default=datetime.utcnow())
	author_id =	Column(Integer, ForeignKey('table1.id'))

	author = relationship('Table1', back_populates='articles')
	comment = relationship('Comment', back_populates='post',lazy='dynamic')

	@staticmethod
	def art_html(target, value, oldvalue, initiator):
		#event.listen(Post.article, 'set', Post.art_html)
		#target是Post对象
		#value是监听到的Post.article
		#oldvalue 无值
		#initiator是根据set的orm.event对象？
		#markdown 将markdown文本转化成html，bleach-clean清除html中不合法的标记
		#linkify是将文本中的网址转化成可点击的。
		#为什么不用__init__?因为__init__在插入post对象之前执行，而那时article没有值
		#无法转化成html
		#clean的清除，并不彻底，只是将不符的tag直接显示出去，而不生效

		target.article_html = bleach.linkify(bleach.clean(markdown(value, output_format='html5'), 
					tags=['a', 'abbr', 'acronym', 'b', 'blockquote', 
					'code','em', 'i', 'li', 'ol', 'pre', 'strong', 
					'ul', 'h3', 'p']))

	@staticmethod
	def insert_post(count):
		from random import randint
		import forgery_py
		db_session=DBSession
		user_count = db_session.query(Table1).count()
		for i in range(count):
			auth = db_session.query(Table1).offset(randint(0,user_count-1)).first()
			newPost=Post(article=forgery_py.lorem_ipsum.sentences(randint(1,3)),
					 post_time=forgery_py.date.date(True),
					 author=auth)
			db_session.add(newPost)

			#而这一段，因为没有__init__，所以可以多次添加add，一次性commit
		try:
			db_session.commit()
		except:
			db_session.rollback()
			raise
		finally:
			print ('bbbbbbbbbbbbbbbb')			
			db_session.close()
event.listen(Post.article, 'set', Post.art_html)

class Permission():
	#-----------------------action below-----------------
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE = 0x04
	SHUTDOWN = 0x08
	ADMIN = 0x80

class Pagination():

	'''
	该类返回需要在每个页面下面渲染的页数列表
	根据当前页面数，返回每页应该渲染的查询对象
	判断是否还有’前一页‘或者’后一页‘
	'''


	def __init__(self, db_session ,art_obj,per_page=5):
	
		from math import ceil
		self.db_session=db_session
		self.per_page=per_page
		self.art_num = art_obj.count()
		self.pages = ceil(self.art_num/self.per_page)
		self.art_obj = art_obj
	
	def iter_pages(self):
		#返回页数列表
		return range(1,self.pages+1)
	
	def render(self,current_page):
		list1 = range(1,self.pages+1)
		newList = []
		for i in list1:
			if abs(i-current_page)<3:
				newList.append(i)
		if len(list1) < 8:
			return list1
		
		elif newList[0]==1:
			newList.append('...')
			newList.append(list1[-1])
			return newList
		elif newList[-1] == list1[-1]:
			newList.insert(0,1)
			newList.insert(1,'...')
			return newList
		else:
			newList.append('...')
			newList.append(list1[-1])
			newList.insert(0,1)
			newList.insert(1,'...')
			return newList
		
	#-------------------------------------
	
	def item(self,current_page):
		#返回每页的post查询对象
		return self.art_obj.offset(self.per_page*(current_page-1)).limit(self.per_page).all()
		
	def has_pre(self, current_page):
		#看是否在第一页
		if current_page==1:
			return False
		else:
			return True
			
	def has_next(self, current_page):
		#看是否在最后一页
		if current_page==self.pages:
			return False
		return True

		
		

#----------------下面这个类继承自AnonymousUserMixin，他所以具有所有之前未登录用户的特征
#----------------此类的功能就是在原有的anoymoususer基础上添加了can和is_admion功能
#----------------并将anonymous_user指向此类，因为此类继承原有功能和新添加的2个功能
#----------------因此实现了向anonymous添加功能的作用
class AnonymousUser(AnonymousUserMixin):
	def can(self, action):
		return False
	def is_admin(self):
		return False
	def followed():
		return None
	def followed_list(self):
		return []
	def followed_article(self):
		db_session=DBSession		
		return db_session.query(Post)
login_manager.anonymous_user = AnonymousUser
#--------------------------------------------------------------------------------

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
	#Role.insert_role()
	#Table1.insert_message(30)
	#Post.insert_post(40)
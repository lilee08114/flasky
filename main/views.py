from . import main
from flask import render_template, flash, request,redirect,url_for
from flask_login import login_required, current_user
from ..forms import EditProfile,for_manager_editor,show_latest_articles,edit_my_article
from ..data_model import DBSession, Table1, Permission, Role, Post, Pagination, Follow
from ..decorator import need_permission
from datetime import datetime
import bleach
from markdown import markdown

@main.route('/', methods=['GET','POST'])
def home_page():
	form = show_latest_articles()
	form2 = edit_my_article()
	art_id = request.args.get('id',0,type=int)
	show_follow = bool(request.cookies.get('show_follow',''))
	print ('id is；',art_id)
	db_session=DBSession
	art = db_session.query(Post).filter_by(id=art_id).first()

	#-------------------------------------------
	if show_follow:
		art_obj = current_user.followed_article()
		pag = Pagination(db_session=db_session, art_obj=art_obj)
	else:
		art_obj = db_session.query(Post)
		pag = Pagination(db_session=db_session,art_obj=art_obj)
	
	current_page = request.args.get('page', 1, type=int) #获取当前页面页数，默认为1
	pag_list = pag.render(current_page)  #页号序列
	pag_item = pag.item(current_page) #每页对应的查询对象
	pre=pag.has_pre(current_page) #是否还有前一页
	nex=pag.has_next(current_page)  #时候还有后一页

	if form2.validate_on_submit():
		art.article = form2.edit_message.data
		art.article_html=bleach.linkify(bleach.clean(markdown(art.article, output_format='html5'), 
					tags=['a', 'abbr', 'acronym', 'b', 'blockquote', 
					'code','em', 'i', 'li', 'ol', 'pre', 'strong', 
					'ul', 'h3', 'p']))
		db_session.add(art)
		db_session.commit()
		flash('your article has been modified!')
		return redirect(url_for('main.home_page'))

	if art_id != 0 and art.author.id==current_user.id:
		form2.edit_message.data = art.article
		art_id = 0
		return render_template('home.html',form=form2, posts=pag_item, state=show_follow,
								current_page=current_page, page_list=pag_list,
								pre=pre, nex=nex,fl=current_user.followed_list())

	
	if form.validate_on_submit() and current_user.can(Permission.WRITE):
		new_post = Post(article = form.post_message.data,
						author_id = current_user.id)
		db_session.add(new_post)
		db_session.commit()
		flash('your message has been uploaded!')
		return redirect(url_for('main.home_page'))
	
	#latest_posts = db_session.query(Post).order_by(Post.post_time.desc()).all()
	return render_template('home.html',form=form, posts=pag_item, state=show_follow,
								current_page=current_page, page_list=pag_list,
								pre=pre, nex=nex, fl=current_user.followed_list())
	#return render_template('navbar.html')
#---------------------------------------------------展示及编辑个人资料页	
@main.route('/profile/<username>/')
@login_required
def show_profile(username):
	'''
	可以使用表格来排版？
	'''
	db_session=DBSession
	#这里使用filter(username==username)居然是无效的！
	target_user=db_session.query(Table1).filter_by(username=username).first()
	#这里为什么是Post.post_time....
	article_obj = target_user.articles.order_by(Post.post_time.desc()).all()
	return render_template('show_profile.html',target_user=target_user,article_object=article_obj)
	
@main.route('/edit_profile/', methods=['GET','POST'])
@login_required
def edit_profile():
	'''
	仍然有逻辑问题，为什么current_user不能直接用？
	个人资料页面，应该对任意人开放，但编辑只对自己开放

	'''
	form = EditProfile()
	if form.validate_on_submit():
		
		db_session = DBSession
		temp = db_session.query(Table1).filter_by(id=current_user.id).first()
		temp.realname = form.realname.data
		temp.gender = form.gender.data
		temp.age = form.age.data
		temp.location = form.location.data
		temp.introduction = form.introduction.data
		
		db_session.add(temp)
		db_session.commit()
		flash('your profile has beem modified！')
		db_session.close()
		return render_template('edit_profile.html', form=form)

	form.realname.data = current_user.realname
	form.gender.data = current_user.gender	 
	form.age.data = current_user.age
	form.location.data = current_user.location
	form.introduction.data = current_user.introduction
	return render_template('edit_profile.html', form=form)
#------------------------------------------------------------------

@main.route('/manager_system/',methods=['GET','POST'])
@need_permission(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE|Permission.SHUTDOWN)
def manager_chart():
	if request.method == 'POST':
		db_session=DBSession
		temp = db_session.query(Table1).filter_by(usermail=request.form['mail']).first()
		if temp is None:
			flash('this user is not exist!')
			return render_template('main/manager_system.html')
		else:
			return redirect(url_for('main.manager_editor',usermail=request.form['mail']))
	return render_template('main/manager_system.html')


@main.route('/edit_profile_manager/<usermail>', methods=['GET','POST'])
@need_permission(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE|Permission.SHUTDOWN)
def manager_editor(usermail):
	form = for_manager_editor()
	db_session=DBSession
	user = db_session.query(Table1).filter_by(usermail=usermail).first()
	form.role.choices = [(temp.id, temp.name) for temp in db_session.query(Role).filter(Role.permission<80).all()]
	#form.role.choices = [(temp.id, temp.name) for temp in Role.query().filter(permission<80).all()]
	form.role.default = user.id

	if form.validate_on_submit():
		user.confrim = form.confirm_state.data
		user.role = db_session.query(Role).filter(Role.id==form.role.data).first()
		user.location = form.location.data
		db_session.add(user)
		db_session.commit()
		flash('%s\'s profile has been mdified'%user.username)
		db_session.close()
		
		return render_template('main/manager_editor.html',form=form)
	confirm_state = user.confirm
	location = user.location
	return render_template('main/manager_editor.html', form=form)

@main.route('/article_detail/')
def article_detail():
	db_session=DBSession
	art_id = request.args.get('id',type=int)
	post = db_session.query(Post).filter_by(id=art_id).first()
	return render_template('article_detail.html', post=post)

@main.route('/follow/<int:his_id>')
@need_permission(Permission.FOLLOW)
@login_required
def followsomeone(his_id):
	db_session=DBSession
	new_follow = Follow(followed_id = his_id,
				follower_id = current_user.id)	
	try:
		db_session.add(new_follow)
		db_session.commit()
		flash('follow sucessfully, you will recieve his dynamics')
	except:
		db_session.rollback()
		flash('error!')
		raise
	finally:
		db_session.close()
	return redirect(request.args.get('next') or request.referrer)

@main.route('/unsubscribe/<int:his_id>')
@need_permission(Permission.FOLLOW)
@login_required
def unsubscribe(his_id):
	db_session=DBSession
	follow_relation = db_session.query(Follow).filter(Follow.followed_id==his_id).\
		filter(Follow.follower_id==current_user.id).first()
	db_session.delete(follow_relation)
	try:	
		db_session.commit()
		flash('your follow relationship has been removed')
	except:
		db_session.rollback()
		flash('fail yo remove your follow relationship!')
		raise
	finally:
		db_session.close()
	return redirect(request.args.get('next') or request.referrer)

@main.route('/show_my_follow/')		
@login_required
def showOnlyMyFollow():
	resp = redirect(url_for('main.home_page'))
	resp.set_cookie('show_follow', '1', max_age=7*24*60*60)
	return resp

@main.route('/show_all/')
@login_required
def show_all():
	resp = redirect(url_for('main.home_page'))
	resp.set_cookie('show_follow','',max_age=7*24*60*60)
	return resp
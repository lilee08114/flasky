from . import main
from flask import render_template, flash, request,redirect,url_for
from flask_login import login_required, current_user
from ..forms import EditProfile,for_manager_editor
from ..data_model import DBSession, Table1, Permission, Role
from ..decorator import need_permission

@main.route('/')
def home_page():
	return render_template('home.html')
#---------------------------------------------------展示及编辑个人资料页	
@main.route('/profile/<username>/')
@login_required
def show_profile(username):
	'''
	可以使用表格来排版？
	'''
	return render_template('show_profile.html')
	
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
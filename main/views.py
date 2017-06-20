from . import main
from flask import render_template, flash
from flask_login import login_required, current_user
from ..forms import EditProfile
from ..data_model import DBSession, Table1

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

	form = EditProfile()
	print ('ssss',form.validate_on_submit())
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
	print ('pppppppppppp')	
	form.realname.data = current_user.realname
	form.gender.data = current_user.gender	 
	form.age.data = current_user.age
	form.location.data = current_user.location
	form.introduction.data = current_user.introduction
	return render_template('edit_profile.html', form=form)
#------------------------------------------------------------------
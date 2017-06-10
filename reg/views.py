from flask import render_template,redirect, url_for,flash,request,current_app
from . import reg
from ..data_model import Table1, DBSession, init_db
from ..forms import loadForm, regForm, changeCode, Forget_code, SetNewCode,SetNewMail
from flask_login import login_user, current_user, logout_user, login_required
from ..main import main
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from ..email import send_mail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

init_db()

#-------------------------------------登陆视图
@reg.route('/login', methods=['GET','POST'])
def load_in():
	form = loadForm()
	if form.validate_on_submit():
		dbsession = DBSession
		user = dbsession.query(Table1).filter_by(usermail=form.email.data).first()
		dbsession.close()

		if (user is not None) and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			return redirect(url_for('main.home_page'))
		flash ('错误的账号或密码')
			#return redirect(url_for('reg.load_in'))  #??????????????

	return render_template('reg/login.html',form=form)

#-------------------------------------登出视图
@reg.route('/logout')
@login_required
def load_out():
	logout_user()
	return redirect(url_for('main.home_page'))

@reg.route('/')
def test_log():
	return redirect(url_for('reg.load_in'))

#-------------------------------------注册视图
@reg.route('/register',methods=['GET','POST'])
def regis():
	form = regForm()
	if form.validate_on_submit():

		db_session = DBSession
		newUser = Table1(username=form.username.data,
						usermail=form.email.data,
						password = form.password1.data)
		db_session.add(newUser)
		db_session.commit()
		flash('you now are one of us!')
		#user = db_session.query(Table1).filter_by() #为什么不需要建立Table1对象？
		token = newUser.generate_confirm_token()		
		send_mail(newUser.usermail, 'confirm', 'email/confirm_mail',user=newUser, token=token)
		flash('and, a confirm letter has been sent to %s'%newUser.usermail)
		db_session.close()
		
	return render_template('reg/register.html',form=form)

#-------------------------------------确认邮件视图
@reg.route('/confirm/<token>')
@login_required
def confirm(token):

	if current_user.confirm:
		return redirect(url_for('main.home_page'))

	if current_user.verify_token(token):
		current_user.confirm = True
		#print ('check successful')
		return redirect(url_for('main.home_page'))
	else:
		flash('confirm link is invalid or expired')

	return redirect(url_for('reg.re_confirm'))

#-------------------------------------发送确认邮件视图
@reg.route('/re_confirm')
@login_required
def re_confirm():
	token = current_user.generate_confirm_token()
	send_mail(current_user.usermail, 'confirm', 'email/confirm_mail',user=current_user, token=token)
	flash('we have sent another confirm letter to %s'%current_user.usermail)
	return  render_template('home.html')

#-------------------------------------检查邮件确认视图
@reg.before_app_request
def check_confirm():
	print ('re-confirm has been cued')
	if current_user.is_authenticated and (not current_user.confirm) and request.endpoint[:4] != 'reg.':
		return redirect(url_for('reg.re_confirm'))

#-------------------------------------重置密码
@reg.route('/reset_code/', methods=['GET','POST'])
@login_required
def resset_code():
	form = changeCode()
	if form.validate_on_submit():
		if current_user.verify_password(form.previous_code.data):
			if current_user.verify_password(form.new_code1.data):
				print ('密码相同检测成功')
				flash('new code shouldn\'t be the same as the old one!')
				return render_template('reg/reset_code.html',form=form)
			current_user.password = form.new_code1.data
			db_session=DBSession
			try:
				db_session.add(current_user)
				db_session.commit()
			except:
				db_session.rollback()
				raise
			finally:
				db_session.close()
			flash('you have successfully change code')
			return redirect(url_for('main.home_page'))

		else:
			flash('wrong password!')
			return  render_template('reg/reset_code.html',form=form)
	return render_template('reg/reset_code.html',form=form)

#-------------------------------------个人信息视图
@reg.route('/my_profile/')
@login_required
def my_profile():
	return render_template('reg/profile.html')

#-------------------------------------忘记密码
@reg.route('/forget-code/', methods=['GET','POST'])
def forget_code():
	
	form = Forget_code()
	if form.validate_on_submit():
		s = Serializer(current_app.config['SECRET_KEY'], 600)
		token = s.dumps({'resset_code':form.Your_email.data})
		current_user.usermail = form.Your_email.data   #????????????
		send_mail(current_user.usermail, 'Resset Your Code!', 
			  'email/resset_code', token=token)
		flash('a confirm mail has been sent your email')
		return render_template('reg/reset_confirm.html',form=form)
	return render_template('reg/reset_confirm.html',form=form)

#-------------------------------------忘记密码后重设密码
@reg.route('/check_mail/<token>', methods=['GET','POST'])
def check_mail(token):
	s = Serializer(current_app.config['SECRET_KEY'], 600)
	usermail = s.loads(token).get('resset_code')
	form = SetNewCode()
	if form.validate_on_submit():
		db_session = DBSession
		temp_user = db_session.query(Table1).filter_by(usermail=usermail).first()
		temp_user.password = form.new_code1.data
		try:
			db_session.add(temp_user)
			db_session.commit()
		except Exception as e:
			db_session.rollback()
			raise e
		finally:
			db_session.close()
		flash('Your code has been modified')
		return redirect(url_for('main.home_page'))

	return render_template('reg/set_new_code.html',form = form)

#-------------------------------------重设电子邮件

@reg.route('/confirm_mail_address/', methods=['GET','POST'])
@login_required
def ChangeMail():
	form = SetNewMail()
	if form.validate_on_submit():
		s = Serializer(current_app.config['SECRET_KEY'],600)
		token = s.dumps({'new_mail':[form.new_mail.data,current_user.id]})
		send_mail(current_user.usermail, 'Resset Your Email!', 
			  'email/change_mail', token=token)#####
		flash('A confirm letter has been sent to your previous email')
		return render_template('reg/set_new_mail.html',form=form)
	return render_template('reg/set_new_mail.html',form=form)

@reg.route('/set_new_mail/<token>')
def SetnewMail(token):
	s = Serializer(current_app.config['SECRET_KEY'],600)
	user = s.loads(token).get('new_mail')
	db_session=DBSession
	temp_user2 = db_session.query(Table1).filter_by(id = user[1]).first()
	temp_user2.usermail = user[0]
	db_session.add(temp_user2)
	db_session.commit()
	db_session.close()
	flash('your email address has been changed!')
	return redirect(url_for('main.home_page'))





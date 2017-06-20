from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, 		 				SelectField, IntegerField, DateTimeField
from wtforms.validators import Required, Email, Length,EqualTo
from .data_model import Table1, DBSession
from wtforms import ValidationError

class loadForm(FlaskForm):
	email = StringField('Email', validators=[Required(),Length(1,64),Email()])
	#username = StringField('Username', validators=[Required()])
	password = PasswordField('Password', validators=[Required()])
	remember_me = BooleanField('Remember me ?')
	submit = SubmitField('Log in')


class regForm(FlaskForm):
	email = StringField('Email', validators=[Required(), Email()])
	username = StringField('username', validators=[Required(), Length(5,64)])
	password1 = PasswordField('password', validators=[Required(),
							EqualTo('password2', message='code not same')])
	password2 = PasswordField('confirm password',validators=[Required()])
	submit = SubmitField('register!')

	def validate_email(self, field): #validate. 方法将和常规验证函数一起调用
		db_session = DBSession
		if db_session.query(Table1).filter_by(usermail=field.data).first():
			raise ValidationError('Email already used')
		db_session.close()

	def validate_username(self, field):
		db_session = DBSession
		if db_session.query(Table1).filter_by(username=field.data).first():
			raise ValidationError('Username already used')

class changeCode(FlaskForm):
	previous_code = PasswordField('previous code', validators=[Required()])
	new_code1 = PasswordField('new code', validators=[Required(), 
							EqualTo('new_code2', message='code not the same')])
	new_code2 = PasswordField('new code again', validators=[Required()])
	submit = SubmitField('Submit')


class Forget_code(FlaskForm):
	Your_email = StringField('Your Email',validators=[Required(), Email()])
	confirm_email = StringField('Confirm Email', validators=[Required(), 
								EqualTo('Your_email',message='email address not the same')])
	submit = SubmitField('submit')

	def validate_Your_email(self, field):
		db_session = DBSession
		if not db_session.query(Table1).filter_by(usermail=field.data).first():
			raise ValidationError('This email haven\'t been registered, register first')

class SetNewCode(FlaskForm):
	new_code1 = PasswordField('New code', validators=[Required(),
									EqualTo('new_code2',message='code not the same')])
	new_code2 = PasswordField('Repeat code', validators=[Required()])
	submit = SubmitField('submit')

class SetNewMail(FlaskForm):
	new_mail = StringField('New Mail', validators=[Required(), Email()])
	submit = SubmitField('submit')
	
class EditProfile(FlaskForm):
	realname = StringField('Real name', validators=[Length(0,8)])
	gender = SelectField('Gender', choices=[('Man','Man',),('Woman','Woman',)])
	age = IntegerField('Age')
	location = StringField('Location', validators=[Length(0,64)])
	introduction = StringField('Introduction')
	submit = SubmitField('submit')
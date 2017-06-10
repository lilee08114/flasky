from flask_mail import Message
from .. import create_app
from flask import render_template
from .. import mail
from threading import Thread

app = create_app()

def send_async_email(app, msg):
	with app.app_context():
		mail.send(msg)

def send_mail(to, subject, template, **kwargs):
	message = Message(app.config['SUBJECT_PREFIX'] + subject,
					  sender = app.config['MAIL_SENDER'],
					  recipients = [to])
	message.body = render_template(template+'.txt',**kwargs)
	message.html = render_template(template+'.html', **kwargs)

	thr = Thread(target=send_async_email, args=[app, message])
	thr.start()
	return thr


from flask_login import current_user
from functools import wraps
from flask import abort



def need_permission(action):
		def f(func):
			@wraps(func)
			def d(*args, **kwargs):
				#print (current_user.role.permission)
				if current_user.can(action):
					return func(*args, **kwargs)
				else:
					abort(403)
			return d
		return f
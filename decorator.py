from flask_login import current_user
from functools import wraps




def need_permission(action):
		def f(func):
			@wraps(func)
			def d(*args, **kwargs):
				if current_user.can(action):
					return func(*args, **kwargs)
				else:
					abort(403)
			return d
		return f
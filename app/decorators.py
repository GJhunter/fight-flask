#coding=utf-8
from functools import wraps
from flask import abort
from flask.ext.login import current_user
from .models import Permission

def permission_required(permission):
	def decorator(f):
		@wraps(f)#wraps装饰器的作用是将__name__、module、__doc__和 __dict__都复制到封装函数,
		#当你调用被装饰函数f.__doc__时他还是会显示f自己的文档字符串
		def decorated_function(*args,**kwargs):
			if not current_user.can(permission):
				abort(403)
			return f(*args,**kwargs)
		return decorated_function
	return decorator

def admin_required(f):
	return permission_required(Permission.ADMINISTER)(f)
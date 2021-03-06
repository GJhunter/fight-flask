 #!/usr/bin/env python
#coding=utf-8
#上面这条声明让程序在unix系统中可以通过./manage.py执行脚本
import os
COV = None
if os.environ.get('FLASK_COVERAGE'):
	import coverage
	COV = coverage.coverage(branch=True,include='app/*')
	COV.start()

from app import create_app,db
from app.models import User,Role,Post,Permission,Follow,Comment
from flask.ext.script import Manager,Shell
from flask.ext.migrate import Migrate,MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')#os.getenv用来读取环境变量
manager = Manager(app)
migrate = Migrate(app,db)


def make_shell_context():
	return dict(app=app,db=db,User=User,Follow=Follow,Role=Role,Permission=Permission,Post=Post)
	
manager.add_command('shell',Shell(make_context=make_shell_context))#集成python shell

manager.add_command('db',MigrateCommand)

@manager.command#自定义命令，命令名即函数名，python manage.py test
def test(coverage=False):
	"""Run the unit tests."""
	if coverage and not os.environ.get('FLASK_COVERAGE'):
		import sys
		os.environ['FLASK_COVERAGE'] = '1'
		os.execvp(sys.executable,[sys.executable] + sys.argv)#重新开始一个进程，sys.executable相当于python
		#解释程序，sys.argv是当前程序的路径，即相当于重启本程序
	import unittest
	tests = unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)
	if COV:
		COV.stop()
		COV.save()
		print('Coverage Summary:')
		COV.report()
		basedir = os.path.abspath(os.path.dirname(__file__))
		covdir = os.path.join(basedir,'tmp/coverage')
		COV.html_report(directory=covdir)
		print ('HTML version:file://%s/index.html' % covdir)
		COV.erase()

	@manager.command
	def profile(length=25,profile_dir=None):
		"""Start the application under the code profiler."""
		from werkzeug.contrib.profiler import ProfilerMiddleware
		app.wsgi_app = ProfilerMiddleware(app.wsgi_app,restrictions=[length],
											profile_dir=profile_dir)
		app.run()

	@manager.command
	def deploy():
		"""Run deployment tasks."""
		from flask.ext.migrate import upgrade
		from app.models import Role,User

		upgrade()

		Role.insert_roles()

		User.add_self_follows()




if __name__ == '__main__':
	manager.run()
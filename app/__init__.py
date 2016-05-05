#coding=utf-8
#__init__.py只有在包中，这个包才能被导入，当我们导入包的时候，__init__.py会自动运行，帮我们导入多个模块等
from flask import Flask,render_template
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from config import config
from flask.ext.login import LoginManager
from flask.ext.pagedown import PageDown

login_manager = LoginManager()
login_manager.session_protection = 'basic'#session_protection的可选属性有None,'basic','strong',
#当为strong时flask－login会记录客户端ip地址和浏览器的用户代理信息，如果发现异动则登出用户
login_manager.login_view = 'auth.login'#设置登陆页面的端点，因为在蓝本中定义的所以前面要加上蓝本的名字

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()

def create_app(config_name):

	app = Flask(__name__)
	app.config.from_object(config[config_name])#将config中一个类的的配置直接导入程序，
	#也就是变成app.config,这可能是不用导入config中其他类的原因，因为被这个方法实现了
	config[config_name].init_app(app)#暂时这样理解：这里的init_app和下面的那四个是不一样的，这里的是config类里定义的，
	#但是作用都是完成初始化，即bootstrap = Bootstrap(app)，moment = Moment(app)等将app参数传到9-12行中的实例里，
	#或者是完成将配置导入app的工作

	bootstrap.init_app(app)
	mail.init_app(app)
	moment.init_app(app)
	db.init_app(app)
	login_manager.init_app(app)
	pagedown.init_app(app)

	if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)


	from .main import main as main_blueprint
	app.register_blueprint(main_blueprint)#蓝本在工厂函数 create_app() 中注册到程序上

	from .auth import auth as auth_blueprint
	app.register_blueprint(auth_blueprint,url_prefix='/auth')#url_prefix是可选参数，将蓝本中所有路由都加上指定前缀，即变成/auth/login，URL变成http://localhost:5000/auth/login
	
	from .api_1_0 import api as api_1_0_blueprint
	app.register_blueprint(api_1_0_blueprint,url_prefix='/api/v1.0')

	return app

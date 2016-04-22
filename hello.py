# -*- coding:utf-8 -*-
import os
from flask import Flask,render_template,session,redirect,url_for,flash
from flask.ext.script import Manager, Shell
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from flask.ext.migrate import Migrate,MigrateCommand
from flask.ext.mail import Mail,Message
from wtforms import StringField,SubmitField
from wtforms.validators import Required
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))
'''
当"print os.path.dirname(__file__)"所在脚本是以完整路径被运行的， 那么将输出该脚本所在的完整路径，比如：

python d:/pythonSrc/test/test.py

那么将输出 d:/pythonSrc/test

'''

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'#设置密匙防范跨站请求伪造的攻击，app.config字典可用来存储框架、扩展和程序本身的配置
app.config['SQLALCHEMY_DATABASE_URI'] =\
'sqlite:///' + os.path.join(basedir,'data.sqlite')#\的作用表示\所在行和下一行其实是一行，os.path.join的作用是将路径重新组成后返回
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True


app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <gj00403@gmail.com>'


bootstrap = Bootstrap(app)
moment = Moment(app)
mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app,db)
manager = Manager(app)
manager.add_command('db',MigrateCommand)



def make_shell_context():
	return dict(app=app,db=db,User=User,Role=Role)
manager.add_command("shell",Shell(make_context=make_shell_context))#集成python shell




class NameForm(Form):
	name = StringField('What is your name?',validators=[Required()])
	submit = SubmitField('Submit')

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(64),unique=True)
	users = db.relationship('User',backref='role',lazy='dynamic')#backref 参数向 User 模型中添加一个 role 属性,从而定义反向关 系。这一属性可替代 role_id 访问 Role 模型,此时获取的是模型对象,而不是外键的值。

	def __repr__(self):
		return '<Role %r>' % self.name

class User(db.Model):
	__tablename__='users'
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(64),unique=True,index=True)
	role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))#db.ForeignKey() 的参数 'roles.id' 表 明,这列的值是 roles 表中行的 id 值。

	def __repr__(self):
		return '<User %r>' % self.username

def send_email(to,subject,template,**kwargs):
	msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX']+subject,sender=app.config['FLASKY_MAIL_SENDER'],recipients=[to])
	msg.body = render_template(template + '.txt',**kwargs)
	mag.html = render_template(template + '.html',**kwargs)
	mail.send(msg)

@app.route('/',methods=['GET','POST'])
def index():
	form = NameForm()
	if form.validate_on_submit():#会调用字段上附属的 Required() 验证函数。如果名字不为空,就能通过验证,validate_on_ submit() 返回 True
		user = User.query.filter_by(username=form.name.data).first()
		if user is None:
			user = User(username=form.name.data)
			db.session.add(user)
			session['known'] = False
			'''
			if app.config['FLASKY_ADMIN']:
				send_email(app.config['FLASKY_ADMIN'],'New User','mail/new_user',user=user)
			'''
		else:
			session['known'] = True
		session['name'] = form.name.data
		form.name.data = ''
		return redirect(url_for('index'))
	return render_template('index.html',form=form,name=session.get('name'),known = session.get('known',False),current_time=datetime.utcnow())

@app.route('/user/<name>')
def user(name):
	return render_template('user.html',name=name)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'),404


if __name__=='__main__':
	manager.run()



'''

from flask.ext.mail import Message
from hello import mail
msg = Message('test subject',sender='gj00403@gmail.com',recipients=['GJ000@outlook.com'])
msg.body = 'text body'
msg.html = '<b>HTML</b> body'
with app.app_context():
...     mail.send(msg)
'''
#coding=utf-8
from werkzeug.security import generate_password_hash,check_password_hash
from app import create_app,db
from . import db,login_manager
from flask.ext.login import UserMixin,AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app,request
from datetime import datetime
import hashlib
from markdown import markdown
import bleach
from app.exceptions import ValidationError


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))#增加回调函数，接收以unicode字符串形式表示的用户标识符，找到返回用户对象否则返回None

class Comment(db.Model):
	__tablename__='comments'
	id = db.Column(db.Integer,primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	disabled = db.Column(db.Boolean)
	author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))

	@staticmethod
	def on_changed_body(target,value,oldvalue,initiator):
		allowed_tags = ['a','abbr','acronym','b','code','em','i','strong']
		target.body_html =bleach.linkify(bleach.clean(
			markdown(value,output_format='html'),
			tags=allowed_tags,strip=True))

	def to_json(self):
		json_comment = {
			'url':url_for('api.get_comment',id=self.id,_external=True),
			'post':url_for('api.get_post',id=self.post_id,_external=True),
			'body':self.body,
			'body_html':self.body_html,
			'timestamp':self.timestamp,
			'author':url_for('api.get_user',id=self.author_id,_external=True)
		}
		return json_comment

	@staticmethod
	def from_json(json_comment):
		body = json_comment.get('body')
		if body is None or body == '':
			raise ValidationError('comment does not have a body')
		return Comment(body=body)

db.event.listen(Comment.body,'set',Comment.on_changed_body)

class Permission:
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE_ARTICLES = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTER = 0x80

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(64),unique=True)
	default = db.Column(db.Boolean,default=False,index=True)
	permissions = db.Column(db.Integer)
	users = db.relationship('User',backref='role',lazy='dynamic')#backref 参数向 User 模型中添加一个 role 属性,从而定义反向关 系。
	#这一属性可替代 role_id 访问 Role 模型,此时获取的是模型对象,而不是外键的值。
	#lazy属性决定加不加载纪录，dynamic是指不加载纪录但是提供查询

	@staticmethod
	def insert_roles():
		roles = {'User' : (Permission.FOLLOW | 
						   Permission.COMMENT |
						   Permission.WRITE_ARTICLES,True),
				'Moderator' : (Permission.FOLLOW | 
								Permission.COMMENT |
								Permission.WRITE_ARTICLES |
								Permission.MODERATE_COMMENTS,False),
				'Administrator' :(0xff,False)
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role is None:
				role = Role(name=r)
			role.permissions = roles[r][0]
			role.default = roles[r][1]
			db.session.add(role)
		db.session.commit()

	def __repr__(self):
		return '<Role %r>' % self.name


class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer,primary_key=True)
	body = db.Column(db.Text)
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
	body_html = db.Column(db.Text)
	comments = db.relationship('Comment',backref='post',lazy='dynamic')

	def to_json(self):
		json_post = {
			'url':url_for('api.get_post',id=self.id,_external=True),
			'body':self.body,
			'body_html':self.body_html,
			'timestamp':self.timestamp,
			'author':url_for('api.get_user',id=self.author_id,_external=True),
			'comments':url_for('api.get_post_comments',id=self.id,_external=True),
			'comment_count':self.comments.count()
		}
		return json_post

	@staticmethod
	def from_json(json_post):
		body = json_post.get('body')
		if body is None or body == '':
			raise ValidationError('post does not have a body')
		return Post(body=body)

	@staticmethod
	def generate_fake(count):
		from random import seed,randint
		import forgery_py
		
		seed()
		user_count = User.query.count()
		for i in range(count):
			u = User.query.offset(randint(0,user_count - 1)).first()#offset(x)可以让查询的结果从第x+1个开始显示（总的排序按query.all()）
			p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
				timestamp=forgery_py.date.date(True),
				author=u)
			db.session.add(p)
			db.session.commit()

	@staticmethod
	def on_changed_body(target,value,oldvalue,initiator):
		allowed_tags = ['a','abbr','acronym','b','blockquote','code',
						'em','i','li','ol','pre','strong','ul',
						'h1','h2','h3','p']
		target.body_html = bleach.linkify(bleach.clean(
			markdown(value,output_format='html'),
			tags=allowed_tags,strip=True))#markdown方法先把Markdown文本转换成HTML，
		#然后clean方法删除不可用的标签，最后linkify把文本中的url转换成链接

db.event.listen(Post.body,'set',Post.on_changed_body)#这个函数监听Post.body只要有新的改动就调用Post.on_changed_body
#应该就是通过这个函数个给on_changed_body传入参数的

class Follow(db.Model):
	__tablename__ = 'follows'
	follower_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
	followed_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
	timestamp = db.Column(db.DateTime,default=datetime.utcnow)


class User(UserMixin,db.Model):#UserMixin类中实现了一些用来记录用户登录状态方法
	__tablename__='users'
	id = db.Column(db.Integer,primary_key=True)
	email = db.Column(db.String(64),unique = True,index=True)
	username = db.Column(db.String(64),unique=True,index=True)
	role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))#db.ForeignKey() 的参数 'roles.id' 表 明,这列的值是 roles 表中行的 id 值。
	confirmed = db.Column(db.Boolean,default=False)
	password_hash = db.Column(db.String(128))
	name = db.Column(db.String(64))
	location = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	member_since = db.Column(db.DateTime(),default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(),default=datetime.utcnow)
	avatar_hash = db.Column(db.String(32))
	posts = db.relationship('Post',backref='author',lazy='dynamic')
	comments = db.relationship('Comment',backref='author',lazy='dynamic')

	followed = db.relationship('Follow',
								foreign_keys=[Follow.follower_id],
								backref=db.backref('follower',lazy='joined'),
								lazy='dynamic',
								cascade='all,delete-orphan')

	followers = db.relationship('Follow',
								foreign_keys=[Follow.followed_id],
								backref=db.backref('followed',lazy='joined'),
								lazy='dynamic',
								cascade='all,delete-orphan')

	def __init__(self,**kwargs):
		super(User,self).__init__(**kwargs)
		if self.role is None:
			if self.email == current_app.config['FLASKY_ADMIN']:
				self.role = Role.query.filter_by(permissions=0xff).first()
			if self.role is None:#不明白为什么还要写一个self.role is None
				self.role = Role.query.filter_by(default=True).first()
		if self.email is not None and self.avatar_hash is None:
			self.avatar_hash = hashlib.md5(
				self.email.encode('utf-8')).hexdigest()#利用email生成MD5散列值，以生成用户头像的url链接

	def to_json(self):
		json_user = {
			'url':url_for('api.get_post',id=self.id,_external=True),
			'username':self.username,
			'member_since':self.member_since,
			'last_seen':self.last_seen,
			'posts':url_for('api.get_user_posts',id=self.id,_external=True),
			'followed_posts':url_for('api.get_user_followed_posts',id=self.id,_external=True),
			'post_count':self.posts.count()	
		}
		return json_user		

	@property
	def followed_posts(self):
	    return Post.query.join(Follow,Follow.followed_id == Post.author_id)\
	    	.filter(Follow.follower_id == self.id)
	

	@property
	def password(self):
	    raise AttributeError('password is not a readable attribute')

	@password.setter
	def password(self,password):
		self.password_hash = generate_password_hash(password)

	'''
	python 内置的@property装饰器可以将一个方法变成属性调用，详情见http://www.liaoxuefeng.com/wiki/001374738125095c955c1e6d8bb493182103fac9270762a000/001386820062641f3bcc60a4b164f8d91df476445697b9e000
	在这里User.password会引发属性错误，User.password(password)会生成密码的散列值
	'''

	def verify_password(self,password):
		return check_password_hash(self.password_hash,password)#查看密码是否正确

	

	def generate_confirmation_token(self,expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'],expiration)
		return s.dumps({'confirm':self.id})

	def confirm(self,token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed=True
		db.session.add(self)
		return True

	def generate_reset_token(self,expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'],expiration)
		return s.dumps({'reset':self.id})

	def reset_password(self,token,new_password):
		s = Serializer(current_app.config['SECRET_KEY'],expiration)
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('reset') != self.id:
			return False
		self.password = new_password
		db.session.add(self)
		return True

	def generate_email_change_token(self,new_email,expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'],expiration)
		return s.dumps({'change_email':self.id,'new_email':new_email})

	def change_email(self,token):
		s = Serializer(current_app['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get['change_email'] != self.id:
			return False
		new_email = data.get['new_email']
		if new_email is None:
			return False
		if self.query.filter_by(email=new_email).first() is not None:
			return False
		self.email = new_email
		self.avatar_hash = hashlib.md5(
				self.email.encode('utf-8')).hexdigest()
		db.session.add(self)
		return True

	def can(self,permissions):
		return self.role is not None and (self.role.permissions & permissions) == permissions
		#用位运算来查看用户是否有该权限

	def is_administrator(self):
		return self.can(Permission.ADMINISTER)
		#检查是否有管理员的权限

	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)
		#用来更新用户登录的时间即last_seen

	def gravatar(self,size=100,default='identicon',rating='x'):
		if request.is_secure:#如果request请求是通过安全协议请求的（如HTTP协议）
			url = 'https://secure.gravatar.com/avatar'
		else:
			url = 'https://www.gravatar.com/avatar'
		hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
		return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
			url=url,hash=hash,size=size,default=default,rating=rating)#format方法可以用来格式化字符串
		#s是指图片大小，r是指图片级别，d是指没有注册gravatar的用户使用的默认图片生成方式。

	@staticmethod
	def generate_fake(count=100):
		from sqlalchemy.exc import IntegrityError
		from random import seed,randint
		import forgery_py

		seed()#可能是因为下面要随机生成数据所以调用随机数种子
		for i in range(count):
			u=User(email=forgery_py.internet.email_address(),
				username = forgery_py.internet.user_name(True),
				password=forgery_py.lorem_ipsum.word(),
				confirmed=True,
				name=forgery_py.name.full_name(),
				location=forgery_py.address.city(),
				about_me=forgery_py.lorem_ipsum.sentence(),
				member_since=forgery_py.date.date(True))
			db.session.add(u)
			try:
				db.session.commit()
			except IntegrityError:#如果出现相同用户名邮件地址就会出现此错误
				db.session.rollback()

	@staticmethod
	def add_self_follows():
		for user in User.query.all():
			if not user.is_following(user):
				user.follow(user)
				db.session.add(user)
				db.session.commit()

	def follow(self,user):
		if not self.is_following(user):
			f = Follow(follower=self,followed=user)
			db.session.add(f)

	def unfollow(self,user):
		f = self.followed.filter_by(followed_id=user.id).first()
		if f:
			db.session.delete(f)

	def is_following(self,user):
		return self.followed.filter_by(followed_id=user.id).first() is not None

	def is_followed_by(self,user):
		return self.followers.filter_by(follower_id=user.id).first() is not None

	def generate_auth_token(self,expiration):
		s = Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
		return s.dumps({'id':self.id})

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return None
		return User.query.get(data['id'])

	def __repr__(self):
		return '<User %r>' % self.username

class AnonymousUser(AnonymousUserMixin):
	def can(self,permissions):
			return False

	def is_administrator(self):
			return False

login_manager.anonymous_user = AnonymousUser
	



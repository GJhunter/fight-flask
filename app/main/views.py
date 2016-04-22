#coding=utf-8
from datetime import datetime
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app,make_response
from . import main
from .forms import NameForm,EditProfileForm,EditProfileAdminForm,PostForm,CommentForm
from .. import db
from ..models import User,Permission,Role,Post,Comment
from ..decorators import admin_required,permission_required
from flask.ext.login import login_required,current_user

@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'

@main.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		db.session.add(current_user)
		flash('Your profile has been updated.')
		return redirect(url_for('.user',username=current_user.username))
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit_profile.html',form=form)

@main.route('/edit_profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user=user)
	if form.validate_on_submit():
		user.email = form.email.data
		user.username = form.username.data
		user.confirmed = form.confirmed.data
		user.role = Role.query.get(form.role.data)
		user.name = form.name.data
		user.location = form.location.data
		user.about_me = form.about_me.data
		db.session.add(user)
		flash('The profile has been updated.')
		return redirect(url_for('.user',username=user.username))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit_profile.html',form=form,user=user)



@main.route('/',methods=['GET','POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and \
			form.validate_on_submit():
		post = Post(body=form.body.data,author=current_user._get_current_object())#这里要用真正的用户对象因此调用_get_current_object()方法
		db.session.add(post)
		return redirect(url_for('.index'))
	page = request.args.get('page',1,type=int)#这里得到的是一个int型，也就是一个数字，默认1,1代表这个路由渲染第一页，当然也可以改成其他页
	show_followed = False
	if current_user.is_authenticated():
		show_followed = bool(request.cookies.get('show_followed',''))
	if show_followed:
		query = current_user.followed_posts
	else:
		query = Post.query
	pagination = query.order_by(Post.timestamp.desc()).paginate(
		page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
		error_out=False)#传入渲染的页数和每页的纪录数
	#可选参数为 error_ out,当其设为 True 时(默认值),如果请求的页数超出了范围,则会返回 404 错误;如果 设为 False,页数超出范围时会返回一个空列表。
	posts = pagination.items
	return render_template('index.html',form=form,posts=posts,
							show_followed=show_followed,pagination=pagination)


@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page',1,type=int)
	pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
		page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
		error_out=False)
	#posts = user.posts.order_by(Post.timestamp.desc()).all()
	posts = pagination.items
	return render_template('user.html',user=user,posts=posts,pagination=pagination)

@main.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body=form.body.data,post=post,author=current_user._get_current_object())
		db.session.add(comment)
		flash('Your comment has been published')
		return redirect(url_for('.post',id=post.id,page=-1))
	page = request.args.get('page',1,type=int)
	if page == -1:
		page = (post.comments.count() -1 )/current_app.config['FLASKY_POSTS_PER_PAGE'] + 1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
		page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
	comments = pagination.items	
	return render_template('post.html',posts=[post],form=form,comments=comments,pagination=pagination)

@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user !=post.author and \
			not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.body.data
		db.session.add(post)
		flash('The post has been updated.')
		return redirect(url_for('.post',id=post.id))
	form.body.data = post.body
	return render_template('edit_post.html',form=form)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	if current_user.is_following(user):
		flash ('You are already following this user.')
		return redirect(url_for('.user',username=username))
	current_user.follow(user)
	flash('You are now following %s. ' % username)
	return redirect(url_for('.user',username=username ))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	if not current_user.is_following(user):
		flash ('You are not following this user')
		return redirect(url_for('.user',username=username))
	current_user.unfollow(user)
	flash('You are not following  %s anymore. ' % username)
	return redirect(url_for('.user',username=username ))

@main.route('/followers/<username>')
def followers(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	page = request.args.get('page',1,type=int)
	pagination = user.followers.paginate(
		page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
		error_out=False)
	follows = [{'user':item.follower,'timestamp':item.timestamp}
			for item in pagination.items]
	return render_template('followers.html',user=user,title='Followers of',
						endpoint='.followers',pagination=pagination,
						follows=follows)

@main.route('/followed-by/<username>')
def followed_by(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	page = request.args.get('page',1,type=int)
	pagination = user.followed.paginate(
				page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
				error_out=False)
	follows = [{'user':item.followed,'timestamp':item.timestamp}
				for item in pagination.items]
	return render_template('followers.html',user=user,title='Followed by',
						endpoint='.followed_by',pagination=pagination,
						follows=follows)


@main.route('/all')
@login_required
def show_all():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed','',max_age=30*24*60*60)
	return resp

@main.route('/followed')
@login_required
def show_followed():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed','1',max_age=30*24*60*60)
	return resp

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
	page = request.args.get('page',1,type=int)
	pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
		page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
		error_out=False)
	comments = pagination.items
	return render_template('moderate.html',comments=comments,pagination=pagination,page=page)

@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = False
	db.session.add(comment)
	return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))

@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = True
	db.session.add(comment)
	return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))

'''
@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
	return "For administrators!"

@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderators_only():
	return "For comment moderator"

@main.route('/normaluser')
@login_required
@permission_required(Permission.FOLLOW)
def for_user():
	return 'For user'









链接：https://www.zhihu.com/question/28688151/answer/66982373
来源：知乎

我的理解是 from . import XXX默认的就是在当前程序所在文件夹里__init__.py程序中导入XXX，如果当前程序所在文件夹里没有__init__.py文件的话，就不能这样写，而应该写成from .A import XXX，A是指当前文件夹下你想导入的函数(或者其他的)的python程序名，如果你想导入的函数不在当前文件夹，
那么就有可能用到 from .. import XXX(即上一个文件夹中的__init__.py)，或者from ..A import XXX(即上一个文件夹中的文件A)

@main.route('/',methods=['GET','POST'])
def index():
		form = NameForm()
		if form.validate_on_submit():#会调用字段上附属的 Required() 验证函数。如果名字不为空,就能通过验证,validate_on_ submit() 返回 True
			user = User.query.filter_by(username=form.name.data).first()
			if user is None:
				user = User(username=form.name.data)
				db.session.add(user)
				session['known'] = False
				
				if app.config['FLASKY_ADMIN']:
					send_email(app.config['FLASKY_ADMIN'],'New User','mail/new_user',user=user)
				
			else:
				session['known'] = True
			session['name'] = form.name.data
			form.name.data = ''
			return redirect(url_for('.index'))#这里的参数用了main.index的简写，如果是跨蓝本的重定向就要用全名
		return render_template('index.html',form=form,name=session.get('name'),known = session.get('known',False),current_time=datetime.utcnow())#这里session.get第二个参数是指找不到'known'时返回Flase
'''

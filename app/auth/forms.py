#coding=utf-8
from flask.ext.wtf import Form
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import Required,Length,Email,Regexp,EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(Form):
	email = StringField('Email',validators=[Required(),Length(1,64),Email()])
	password = PasswordField('Password',validators=[Required()])
	remember_me = BooleanField('Keep me logged in')
	submit = SubmitField('Log In')

class RegistrationForm(Form):
	email = StringField('Email',validators=[Required(),Length(1,64),Email()])
	username = StringField('Username',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,
	'Usernames must have only letters,numbers,dots or underscores')])#Regexp保证用数字户名只能由字母数字等组成，后面两个参数分别是正则表达式的旗标和验证失败时的提示信息
	password = PasswordField('Password',validators=[Required(),EqualTo('password2',message='Password must match.')])
	password2 = PasswordField('Confirm password',validators=[Required()])
	submit = SubmitField('Register')

	def validate_mail(self,field):#表格类中有以validate_开头的方法，这个方法就和常规的验证函数一起调用
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('Email already registered.')
		
	def validate_username(self,field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('Username already in use.')

class ChangePasswordForm(Form):
	old_password = PasswordField('Old password',validators=[Required()])
	password = PasswordField('New password',validators=[Required(),EqualTo('password2',message='Password must match')])
	password2 = PasswordField('Confirm new password',validators=[Required()])
	submit = SubmitField('Update Password')

class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('New Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')

class ChangeEmailForm(Form):
	email = StringField('New Email',validators=[Required(),Length(1,64),Email()])
	password = PasswordField('Password',validators=[Required()])
	submit = SubmitField('Update Email Address')

	def validate_email(self,field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('Email already registered.')












#coding=utf-8
import unittest
from flask import current_app
from app import create_app,db

class BasicsTestCase(unittest.TestCase):
	def setUp(self):
		self.app = create_app('testing')#用工厂函数创建应用
		self.app_context = self.app.app_context()#app.app_context可以创建一个程序上下文
		self.app_context.push()
		db.create_all()#create_all函数可以根据模型类创建数据库，即生成一个XXX.sqlite文件

	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()

	def test_app_exists(self):
		self.assertFalse(current_app is None)

	def test_app_is_testing(self):
		self.assertTrue(current_app.config['TESTING'])#即检查app.config，当前应用的环境变量
		


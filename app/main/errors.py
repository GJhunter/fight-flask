#coding=utf-8
from flask import render_template,request,jsonify
from . import main


@main.app_errorhandler(403)
def forbidden(e):
	if request.accept_mimetypes.accept_json and \
			not request.accept_mimetypes.accept_html:
		response = jsonify({'error':'forbidden'})
		response.status_code = 403
		return response
	return render_template('403.html'),403


@main.app_errorhandler(404)#在蓝本中编写错误处理程序稍有不同,如果使用 errorhandler 修饰器,那么只有蓝本中的
#错误才能触发处理程序。要想注册程序全局的错误处理程序,必须使用 app_errorhandler
def page_not_found(e):
	if request.accept_mimetypes.accept_json and \
			not request.accept_mimetypes.accept_html:
		response = jsonify({'error':'not found'})
		response.status_code = 404
		return response
	return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
	if request.accept_mimetypes.accept_json and \
			not request.accept_mimetypes.accept_html:
		response = jsonify({'error':'internal server error'})
		response.status_code = 500
		return response
	return render_template('500.html'),500




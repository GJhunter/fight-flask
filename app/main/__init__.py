#coding=utf-8
from flask import Blueprint

main = Blueprint('main',__name__)

from . import views,errors
from ..models import Permission

@main.app_context_processor
def inject_permissions():
	return dict(Permission=Permission)
#上下文处理器，能让变量在所有模板中全局可访问å


'''

链接：https://www.zhihu.com/question/28688151/answer/66982373
来源：知乎

rom . import XXX默认的就是在当前程序所在文件夹里__init__.py程序中导入XXX
'''
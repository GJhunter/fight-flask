#-*- coding: utf-8 -*-
'''
export MAIL_USERNAME='gj00403@gmail.com'
export MAIL_PASSWORD='gaojian20'
export FLASKY_ADMIN='gj00403@gmail.com'
'''
try:
    x = 1
    y = 'f'
    print x/y
except (ZeroDivisionError,TypeError),e:
    print e
    print type(e)

a = ('asdfasdf',)
print type(a)
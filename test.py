from flask import Flask,make_response,abort

app = Flask(__name__)

@app.route('/')
def index():
	response = make_response('<h1>This document carries a cookie</h1>')
	response.set_cookie('answer','42')
	return response

@app.route('/user/<id>')
def get_user(id):
	user = load_user(id)
	if not user:
		abort(404)
	return '<h1>Hello,%s</h1>' % user.name

if __name__ == '__main__':
	app.run(debug=True)
from . import main
from flask import render_template


@main.route('/')
def home_page():
	return render_template('home.html')
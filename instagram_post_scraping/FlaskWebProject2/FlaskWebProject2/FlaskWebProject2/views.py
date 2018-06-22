"""
Routes and views for the flask application.
"""

from datetime import datetime

from flask import render_template, redirect, request

from FlaskWebProject2 import app
from FlaskWebProject2.models.factory import create_repository
from FlaskWebProject2.settings import REPOSITORY_NAME, REPOSITORY_SETTINGS

repository = create_repository(REPOSITORY_NAME, REPOSITORY_SETTINGS)

@app.route('/')
@app.route('/home')
def home():
    """Renders the home page, with a list of all polls."""
    return render_template(
        'index.html',
        title='Welcome',
        year=datetime.now().year,
        #links=repository.getLinks()
    )

@app.route('/get_content', methods=['GET', 'POST'])
def get_content():
	"""Seeds the database with sample polls."""
	return render_template(
        'post_content.html',
        title='Post content',
        year=datetime.now().year,
		links = repository.getLinks(),
        data=getDataFromPostList_Multithread(links),
		content=exportData(data)
    )

@app.route('/get_links', methods=['GET', 'POST'])
def get_links():
	"""Seeds the database with sample polls."""
	print("Going to url: " + str(request.form['url']))
	repository.setUrlToScrape(request.form['url'])
	links = repository.getLinks()
	return redirect('/post_links')

@app.route('/post_links')
def post_links():
    """Renders the home page, with a list of all polls."""
    return render_template(
        'post_links.html',
        title='Post links',
        year=datetime.now().year,
        links=repository.getLinks()
    )

@app.route('/post_content')
def post_content():
    """Renders the home page, with a list of all polls."""
    return render_template(
        'post_content.html',
        title='Post content',
        year=datetime.now().year,
        #links=repository.getLinks()
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        #repository_name=repository.name,
    )

@app.route('/seed', methods=['POST'])
def seed():
    """Seeds the database with sample polls."""
    #repository.add_sample_polls()
    return redirect('/')

@app.route('/results/<key>')
def results(key):
    """Renders the results page."""
    poll = repository.get_poll(key)
    poll.calculate_stats()
    return render_template(
        'results.html',
        title='Results',
        year=datetime.now().year,
        poll=poll,
    )

@app.route('/poll/<key>', methods=['GET', 'POST'])
def details(key):
    """Renders the poll details page."""
    error_message = ''
    if request.method == 'POST':
        try:
            choice_key = request.form['choice']
            repository.increment_vote(key, choice_key)
            return redirect('/results/{0}'.format(key))
        except KeyError:
            error_message = 'Please make a selection.'

    return render_template(
        'details.html',
        title='Poll',
        year=datetime.now().year,
        poll=repository.get_poll(key),
        error_message=error_message,
    )

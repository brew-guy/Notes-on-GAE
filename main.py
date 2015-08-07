# This file contains the submission material for the Udacity Nanodegree
# Introduction to Programming by Jes H.
#
# Written for Python 2.7
#
# Bootstrap code for Google App Engine to Jinja2 for html templates
# Used to show the course notes

import webapp2
import jinja2
import os
import cgi
import urllib
from google.appengine.api import users
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(
  loader = jinja2.FileSystemLoader(template_dir),
  autoescape = True)

class Handler(webapp2.RequestHandler):
  """Generic Handler; will be inherited by more specific path Handlers"""
  def write(self,*a,**kw):
    "Write strings to the website"
    self.response.out.write(*a,**kw)

  def render_str(self,template,**params):
    "Render Jinja2 templates"
    t = jinja_env.get_template(template)
    return t.render(**params)

  def render(self,template,**kw):
    "Write Jinja2 template to the website"
    self.write(self.render_str(template,**kw))

class MainPage(Handler):
  def get(self):
    # self.write("<a href=""/notes""><h2>Click here to see notes</h2><a>")
    p = self.request.get('p')
    self.render("root_welcome.html", p = p)

class NotesHandler(Handler):
  def get(self):
    p = self.request.get('p')
    q = self.request.get('q','')
    self.render("notes.html", p = p, q = q)

class FizzBuzzHandler(Handler):
  def get(self):
    f = self.request.get('f')
    p = self.request.get('p', 0)
    p = p and int(p)
    self.render('fizzbuzz.html', f = f, p = p)

class PostWall(webapp2.RequestHandler):
  def post(self):
    # We set the same parent key on the 'Post' to ensure each
    # Post is in the same entity group. Queries across the
    # single entity group will be consistent. However, the write
    # rate to a single entity group should be limited to
    # ~1/second.
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    post = Post(parent=wall_key(wall_name))

    # When the person is making the post, check to see whether the person
    # is logged into Google
    if users.get_current_user():
      post.author = Author(
            identity=users.get_current_user().user_id(),
            name=users.get_current_user().nickname(),
            email=users.get_current_user().email())
    else:
      post.author = Author(
            name='anonymous@anonymous.com',
            email='anonymous@anonymous.com')


    # Get the content from our request parameters, in this case, the message
    # is in the parameter 'content'
    post.content = self.request.get('content')

    # Write to the Google Database
    post.put()

    # Do other things here such as a page redirect
    self.redirect('/?wall_name=' + wall_name)

# Part of the Google App Engine code together with MainPage class. Recognizes
# a certain path structure (e.g. '/') and uses the matching class for response.
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/notes', NotesHandler),
                               ('/fizzbuzz', FizzBuzzHandler),
                               ('/sign', PostWall),
                              ], debug=True)

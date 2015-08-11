# This file contains the submission material for the Udacity Nanodegree
# Introduction to Programming by Jes H.
#
# Written for Python 2.7
#
# Google App Engine with Jinja2 applied to show the course notes.
# Commenting functionality per lesson and other stuff implemented.
#
# TODO:
# - get user from the post form input
# - set wall name to lesson name, will it work?


import cgi
import urllib
from google.appengine.api import users
from google.appengine.ext import ndb

# Required to ensure only utf-8 formatted characters are shown
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Jinja and Google App Engine requirements
import os
import webapp2
import jinja2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(
  loader = jinja2.FileSystemLoader(template_dir),
  autoescape = True)

# Google App Engine classes
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
    stage1_list = make_lesson_list(load_stage('templates/notes_stage1_raw.html'))
    stage2_list = make_lesson_list(load_stage('templates/notes_stage2_raw.html'))
    stage3_list = make_lesson_list(load_stage('templates/notes_stage3_raw.html'))
    stage4_list = make_lesson_list(load_stage('templates/notes_stage4_raw.html'))
    stage5_list = make_lesson_list(load_stage('templates/notes_stage5_raw.html'))
    self.render("notes.html",
                p = p,
                q = q,
                stage1 = stage1_list,
                stage2 = stage2_list,
                stage3 = stage3_list,
                stage4 = stage4_list,
                stage5 = stage5_list)

class FizzBuzzHandler(Handler):
  def get(self):
    f = self.request.get('f')
    p = self.request.get('p', 0)
    p = p and int(p)
    self.render('fizzbuzz.html', f = f, p = p)

DEFAULT_WALL = 'Public'

# Wall post/comment classes with Google App Engine Database
# We set a parent key on the 'Post' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.
def wall_key(wall_name=DEFAULT_WALL):
  """Constructs a Datastore key for a Wall entity.
  We use wall_name as the key.
  """
  return ndb.Key('Wall', wall_name)

# These are the objects that will represent our Author and our Post. We're using
# Object Oriented Programming to create objects in order to put them in Google's
# Database. These objects inherit Googles ndb.Model class.
class Author(ndb.Model):
  """Sub model for representing an author."""
  # identity = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=False)
  # email = ndb.StringProperty(indexed=False)

class Post(ndb.Model):
  """A main model for representing an individual post entry."""
  author = ndb.StructuredProperty(Author)
  content = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)

class WallPage(Handler):
  def get(self):
    p = self.request.get('p','')
    wall_name = self.request.get('lesson',DEFAULT_WALL)
    # wall_name = self.request.get('wall_name',DEFAULT_WALL)
    if wall_name == DEFAULT_WALL.lower(): wall_name = DEFAULT_WALL
    # Ancestor Queries, as shown here, are strongly consistent
    # with the High Replication Datastore. Queries that span
    # entity groups are eventually consistent. If we omitted the
    # ancestor from this query there would be a slight chance that
    # Wall Post that had just been written would not show up in a
    # query.

    # [START query]
    posts_query = Post.query(ancestor = wall_key(wall_name)).order(-Post.date)
    # The function fetch() returns all posts that satisfy our query. The function returns a list of
    # post objects
    posts = posts_query.fetch()
    # [END query]

    # If a person is logged into Google's Services
    # user = users.get_current_user()
    # if user:
    #     url = users.create_logout_url(self.request.uri)
    #     url_linktext = 'Logout'
    #     user_name = user.nickname()
    # else:
    #     url = users.create_login_url(self.request.uri)
    #     url_linktext = 'Login'
    #     user_name = 'Anonymous Poster'

    # Create our posts html
    posts_html = ''
    for post in posts:

      # Check if the current signed in user matches with the author's identity from this particular
      # post. Newline character '\n' tells the computer to print a newline when the browser is
      # is rendering our HTML
      # if user and user.user_id() == post.author.identity:
      #   posts_html += '<div><h3>(You) ' + post.author.name + '</h3>\n'
      # else:
      posts_html += '<div><h3>' + post.author.name + '</h3>\n'

      posts_html += 'wrote: <blockquote>' + cgi.escape(post.content) + '</blockquote>\n'
      posts_html += '</div>\n'

    sign_query_params = urllib.urlencode({'wall_name': wall_name})

    # Write Out Page here
    self.render("wallbook.html",
                p = p,
                lesson = wall_name,
                posts = posts_html)

class PostWall(webapp2.RequestHandler):
  def post(self):
    # We set the same parent key on the 'Post' to ensure each
    # Post is in the same entity group. Queries across the
    # single entity group will be consistent. However, the write
    # rate to a single entity group should be limited to
    # ~1/second.
    wall_name = self.request.get('lesson',DEFAULT_WALL)
    post = Post(parent=wall_key(wall_name))
    # When the person is making the post, check to see whether the person
    # is logged into Google
    if users.get_current_user():
      post.author = Author(
            # identity=users.get_current_user().user_id(),
            name=users.get_current_user().nickname())
            # email=users.get_current_user().email())
    else:
      post.author = Author(
            name='A. Nonymous')
            # email='anonymous@anonymous.com')
    # Get the content from our request parameters, in this case, the message
    # is in the parameter 'content'
    post.content = self.request.get('content')
    # Write to the Google Database
    post.put()
    # Do other things here such as a page redirect
    self.redirect('/comment?lesson=' + wall_name)

# Part of the Google App Engine code together with MainPage class. Recognizes
# a certain path structure (e.g. '/') and uses the matching class for response.
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/notes', NotesHandler),
                               ('/fizzbuzz', FizzBuzzHandler),
                               ('/comment', WallPage),
                              ], debug=True)

# Helper functions to read raw stage note template and return list
LESSON_KEY, CONCEPT_KEY, CONCEPT_END = '// LESSON //', '// CONCEPT //', '// CONCEPT END //'

def load_stage(file_name):
  '''Loads lessons + concepts from a text/html course stage file'''
  with open(file_name,'r') as file_input:
    lines = file_input.readlines()
  # lines will be a list that contains all of our lines.
  # We use the String.join technique to join all of our elements in the list
  return ''.join(lines)

def make_lesson_list(text):
  '''Takes the total lessons with concepts text, returns a nested list containing Lesson, Concept Title and Concept Description, [['L1', ['C1', 'D']], ['L2', ['C2', 'D']]]
    To be optimized later for less clunkiness...
  '''
  stage_list = []
  lesson_list = []
  lesson_ready = True
  while text != '':
    next_lesson_start = text.find(LESSON_KEY) + len(LESSON_KEY)+1
    next_lesson_end = text.find(CONCEPT_KEY)-1
    next_concept_start = text.find(CONCEPT_KEY) + len(CONCEPT_KEY)+1
    next_concept_end = text.find(CONCEPT_END)-1
    if (next_lesson_end >= 0 and lesson_ready == True):
      lesson = text[next_lesson_start:next_lesson_end]
      lesson_list.append(lesson)
      text = text[next_lesson_end+1:]
    elif next_concept_end >= 0:
      concept_str = text[next_concept_start:next_concept_end]
      concept_title = concept_str[:concept_str.find('\n')]
      concept_body = concept_str[concept_str.find('\n')+1:]
      concept_list = [concept_title, concept_body]
      lesson_list.append(concept_list)
      text = text[next_concept_end+len(CONCEPT_END)+2:]
      if text.find(LESSON_KEY) == 0:
        stage_list.append(lesson_list)
        lesson_list = []
        lesson_ready = True
      else:
        lesson_ready = False
  if stage_list != []: stage_list.append(lesson_list)
  return stage_list

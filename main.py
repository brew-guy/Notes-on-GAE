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


import urllib
from google.appengine.api import users
from google.appengine.ext import ndb

# Required to ensure only utf-8 formatted characters are shown
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Jinja and Google App Engine libraries and environment variables
import os
import webapp2
import jinja2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(
  loader = jinja2.FileSystemLoader(template_dir),
  autoescape = True)

# -------------------- GOOGLE APP ENGINE WEBPAGE HANDLERS --------------------

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
    p = p and abs(int(p))
    self.render('fizzbuzz.html', f = f, p = p)

# ---------- COMMENT/WALLPOST FUNCTIONALITY USING GAE DATASTORE ----------

# Wall post/comment classes with Google App Engine Datastore
# We set a parent key on the 'Post' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.
def wall_key(wall_name):
  """Constructs a Datastore key for a Wall entity.
  We use wall_name as the key.
  """
  return ndb.Key('Wall', wall_name)

# These are the objects that will represent our Author and our Post. We're using
# Object Oriented Programming to create objects in order to put them in Google's
# Datastore. These objects inherit Googles ndb.Model class.
class Author(ndb.Model):
  """Sub model for representing an author."""
  # I'll just keep it simple and store a user name
  name = ndb.StringProperty(indexed=False)

class Post(ndb.Model):
  """A main model for representing an individual post entry."""
  author = ndb.StructuredProperty(Author)
  content = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)

class WallPage(Handler):
  def get(self):
    p = self.request.get('p','')
    wall_name = self.request.get('lesson')
    # [START query]
    posts_query = Post.query(ancestor = wall_key(wall_name)).order(-Post.date)
    # fetch() returns all posts that satisfy our query and returns a list of post objects
    posts = posts_query.fetch()
    # [END query]
    # Create the posts html to print on the comments pages
    posts_html = ''
    for post in posts:
      # Newline character '\n' tells the computer to print a newline when the browser is
      # rendering the html.
      # We'll build a post consisting of date, time, user name and comment with html allowed:
      posts_html += '<div><h4>On ' + str(post.date.strftime('%d-%b-%Y %H:%M')) + ' ' + post.author.name + ' wrote:</h4>\n'
      posts_html += '<blockquote>' + post.content + '</blockquote>\n'
      posts_html += '</div>\n'
    # These parameters are passed to the input form on the comments page so the form in turn
    # can include those parameters to the Post request. The lesson-wall gets carried over this way
    # from notes --> comments --> Post and is the ancestor key for each Datastore entity (=wall)
    sign_query_params = urllib.urlencode({'wall_lesson': wall_name})
    # Write out the comments page here
    self.render("commentbook.html",
                p = p,
                lesson = wall_name,
                params = sign_query_params,
                posts = posts_html)

class PostWall(webapp2.RequestHandler):
  def post(self):
    # Same parent key on the 'Post' to ensure each Post is in the same entity group.
    # Queries across the single entity group will be consistent.
    #
    # Pluck the lesson and username when sent here from the notes page
    # and create post using the lesson name as Key
    wall_name = self.request.get('wall_lesson')
    post = Post(parent=wall_key(wall_name))
    user_name = self.request.get('user')
    post.author = Author(name=user_name)
    # Get the content from our request parameters, in this case, the message
    # is in the parameter 'comment' from the user submission form
    post.content = self.request.get('comment')
    # Write to the Google Datastore
    post.put()
    # And finally a page redirect back to the comments page with same lesson set as the "wall"
    # This way the user can immediately see his/her new comment added to the top.
    # (It's the lesson-wall ancestor key circling back)
    self.redirect('/comment?lesson=' + wall_name)

# --------------- GOOGLE APP ENGINE PARAMETERS FOR WEBPAGE HANDLERS ---------------

# Part of the Google App Engine code together with MainPage class. Recognizes
# a certain path structure (e.g. '/') and uses the matching class for response.
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/notes', NotesHandler),
                               ('/fizzbuzz', FizzBuzzHandler),
                               ('/comment', WallPage),
                               ('/sign', PostWall),
                              ], debug=True)

# -------- HELPER FUNCTIONS TO READ RAW STAGE NOTE TEMPLATE AND RETURN LIST --------

# Keys that _must_ be used in notes files to mark the content
LESSON_KEY, CONCEPT_KEY, CONCEPT_END = '// LESSON //', '// CONCEPT //', '// CONCEPT END //'

def load_stage(file_name):
  '''Loads lessons + concepts from a text/html course stage file'''
  with open(file_name,'r') as file_input:
    lines = file_input.readlines()
  # lines will be a list that contains all of our lines.
  # We use the String.join technique to join all of our elements in the list
  return ''.join(lines)

# To be optimized later for 1) less clunkiness, 2) validated input, 3) search by regular
# expressions, 4) storage by OOP (stage <-- lesson <-- concept objects)
def make_lesson_list(text):
  '''Takes text file containing all lessons with concepts text, returns a nested list containing Lesson, Concept Title and Concept Description, [['L1', ['C1', 'D']], ['L2', ['C2', 'D']],...]
  '''
  stage_list = [] # Container list for final output
  lesson_list = [] # Intermediate container list for lesson contents
  lesson_ready = True # Gatekeeper for closing/opening a fresh intermediate lesson container
  while text != '': # Loop until the complete text of lessons+concepts is chipped down to nothing
    next_lesson_start = text.find(LESSON_KEY) + len(LESSON_KEY)+1 # Find start index of next lesson
    next_lesson_end = text.find(CONCEPT_KEY)-1 # ...and end index
    next_concept_start = text.find(CONCEPT_KEY) + len(CONCEPT_KEY)+1 # Same procedure for concepts
    next_concept_end = text.find(CONCEPT_END)-1
    if (next_lesson_end >= 0 and lesson_ready == True): # If gate is open, it's time for new lesson
      lesson = text[next_lesson_start:next_lesson_end] # Snip out the lesson headline
      lesson_list.append(lesson) # Store headline in intermediate lesson list
      text = text[next_lesson_end+1:] # Shorten text by lesson key + lesson headline
    elif next_concept_end >= 0: # If gate was closed, it's time to add concepts to the lesson list
      concept_str = text[next_concept_start:next_concept_end] # Snip out the next complete concept
      concept_title = concept_str[:concept_str.find('\n')] # Concept title is first line until CR (\n)
      concept_body = concept_str[concept_str.find('\n')+1:] # Concept description is the rest
      concept_list = [concept_title, concept_body] # Wrap the concept in it's own little list
      lesson_list.append(concept_list) # Add that little concept list to the current lesson list
      text = text[next_concept_end+len(CONCEPT_END)+2:] # Shorten text again to cut away last concept
      if text.find(LESSON_KEY) == 0: # Look what's next in the text. If new lesson is up, it's time to...
        stage_list.append(lesson_list) # Wrap latest intermediate lesson list in stage list
        lesson_list = [] # Clear the intermediate lesson list, so ready for next lesson
        lesson_ready = True # Tell gatekeeper a new lesson is coming up
      else: # If the next in the text wasn't a new lesson, then keep finding concepts
        lesson_ready = False # To find concepts, the gatekeeper must know we're not ready for a new lesson
  if stage_list != []: stage_list.append(lesson_list) # Put last lesson list into the stage list
  return stage_list # Time to return the nicely wrapped up lessons + concepts

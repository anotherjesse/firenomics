import urllib, hashlib, datetime
from vendor import web
from models import *
import sanitize

from google.appengine.api import users

urls = (
  '/forum', 'index',
  '/forum/([^/]*)/new', 'new_topic',
  '/forum/([^/]*)/(.*)', 'topic',
  '/forum/([^/]*)', 'list',
)

render = web.template.render('templates/forum', base='../base')

class index:
    def GET(self):
        topics = db.GqlQuery("SELECT * FROM Topic ORDER BY created DESC LIMIT 10")
        return render.index(topics)

class list:
    def GET(self, tag):
        topics = db.GqlQuery("SELECT * FROM Topic WHERE tags = :1 ORDER BY created", tag)
        return render.list(topics, tag)

class new_topic:
    def GET(self, tag):
        user = users.get_current_user()
        if user:
            return render.new_topic(tag)
        else:
            return web.seeother(users.create_login_url('/forum/%s/new' % tag))

    def POST(self, tag):

        i = web.input()

        topic = Topic()
        topic.title = i.title
        topic.tags = [tag]
        topic.user = users.get_current_user()

        topic.put()
        post = Post()
        post.topic = topic
        post.body = i.body
        post.body_html = sanitize.html(i.body)
        post.user = users.get_current_user()
        post.put()
        return web.seeother("/forum/%s/%s" % (tag, topic.key()))

class topic:
    def GET(self, tag, key):
        topic = Topic.get(key)

        user = users.get_current_user()
        if user:
            login_url = None
        else:
            login_url = users.create_login_url('/forum/%s' % key)
        return render.show(topic, login_url)

    def POST(self, key):
        i = web.input()

        topic = Topic.get(key)
        post = Post()
        post.topic = topic
        post.body = i.body
        post.body_html = sanitize.html(i.body)
        post.user = users.get_current_user()
        post.put()
        return web.seeother("/forum/%s" % topic.key())


app = web.application(urls, globals())
main = app.cgirun()

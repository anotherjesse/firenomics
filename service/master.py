from google.appengine.ext import db
from google.appengine.api import users
from vendor.recaptcha.client import captcha
from vendor import web
from models import *
from utils import analytics
import sanitize, simplejson, uuid, md5, re

urls = (
  '/()', 'static',
  '/(about)', 'static',
  '/(install)', 'static',
  '/(privacy)', 'static',
  '(.*).html', 'redirect',
  '(.+)/', 'redirect',
  '/login', 'login',
  '/logout', 'logout',
  '/home', 'home',
  '/users/(.*)', 'user',
  '/welcome', 'welcome',
  '/extensions', 'extensions',
  '/extensions/(.*)', 'extension',
  '/profile/(.*)', 'profile',
  '(.*)', 'page',
)

render = web.template.render('templates', base='base')
render_no_layout = web.template.render('templates')

class static:
    def GET(self, slug):
        if slug == '': slug = 'index'
        return render.__getattr__(slug)()

class logout:
    def GET(self):
        return web.seeother(users.create_logout_url('/'))


class login:
    def GET(self):
         return web.seeother(users.create_login_url('/welcome'))

def profile_or_home():
    try:
        if web.input().profile:
            return web.seeother("/profile/%s" % web.input().profile)
    except:
        pass
    return web.seeother('/home')

class welcome:
    def GET(self):
        user = db.GqlQuery("SELECT * FROM User WHERE goog = :1", users.get_current_user()).get()
        if not user:
            return render.welcome()
        else:
            return profile_or_home()

    def POST(self):
        user = db.GqlQuery("SELECT * FROM User WHERE goog = :1", users.get_current_user()).get()
        if not user:
            valid_name_regexp = re.compile(r"[a-z]+[a-z_0-9]+")
            if valid_name_regexp.match(web.input().name):
                user = User(key_name=web.input().name)
                user.goog = users.get_current_user()
                user.name = web.input().name
                if user.put():
                    return profile_or_home()
            return render.welcome()

        return profile_or_home()

class profile:
    def GET(self, key):
        try:
            if web.input().login:
                return web.seeother(users.create_login_url("/welcome?profile=%s" % key))
        except:
            pass
        profile = Profile.get(key)
        nonce = uuid.uuid4().hex
        goog = users.get_current_user()
        if profile:
            return render.profile(profile, nonce, goog)
        else:
            return web.seeother('/')

    def POST(self, key):
        goog = users.get_current_user()
        if not goog:
            return web.seeother('/')

        profile = Profile.get(key)
        if not profile:
            web.debug("no such profile")
            return web.seeother('/')
        challenge = web.input().challenge
        response = web.input().response
        secret = profile.secret
        expected_response = md5.new(challenge + secret).hexdigest()
        web.debug("response = " + response + ", expected = " + expected_response)
        user = db.GqlQuery("SELECT * FROM User WHERE goog = :1", goog).get()
        if (expected_response == response) and user:
            web.debug("own the profile")
            profile.user = user
            profile.put()
            return web.seeother("/users/%s" % user.name)
        else:
            web.debug("unauthorized")
            web.ctx.status = "401 unauthorized"
            return web.seeother('/')


class page:
    def GET(self, slug):
        return "Hi"

class user:
    def GET(self, name):
        user = db.GqlQuery("SELECT * FROM User WHERE name = :1", name).get()
        return render.user(user)

class extensions:
    def GET(self):
        extensions = db.GqlQuery("SELECT * FROM Extension ORDER BY name ASC")
        return render.extensions(extensions)

class extension:
    def GET(self, mid):
        extension = db.GqlQuery("SELECT * FROM Extension WHERE mid = :1", mid)[0]
        return render.extension(extension)

def getUser():
    goog = users.get_current_user()
    if goog:
        return db.GqlQuery("SELECT * FROM User WHERE goog = :1", goog).get()

class home:
    def GET(self):
        user = getUser()
        if not user:
            return web.seeother('/login')

        return render.user(user)

class redirect:
    def GET(self, slug):
        web.Redirect(slug)

app = web.application(urls, globals())
main = app.cgirun()

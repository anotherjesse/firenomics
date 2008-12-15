from google.appengine.ext import db
from google.appengine.api import users
from vendor.recaptcha.client import captcha
from vendor import web
from models import *
from utils import analytics
import sanitize
import simplejson
import uuid

PUB = 'FIXME'

urls = (
  '/()', 'static',
  '/(about)', 'static',
  '/(install)', 'static',
  '/(privacy)', 'static',
  '(.*).html', 'redirect',
  '(.+)/', 'redirect',
  '/login', 'login',
  '/logout', 'logout',
  '/forums',  'forum',
  '/forums/feed',  'forum_feed',
  '(.+)/forum', 'topics',
  '(.+)/forum/new', 'newTopic',
  '(.+)/forum/([^/]*)', 'topic',
  '/home', 'update',
  '/users/(.*)', 'user',
  '/welcome', 'welcome',
  '/settings', 'settings',
  '/extensions', 'extensions',
  '/extensions/(.*)', 'extension',
  '/profile/(.*)', 'profile',
  '/update', 'update',
  '/update/(.*)', 'update',
  '(.*)', 'page',
)

#web.template.Template.globals['hack'] = Article
#web.template.Template.globals['analytics'] = analytics
#web.template.Template.globals['card'] = open('templates/partials/card.html').read()
#web.template.Template.globals['rss'] = open('templates/partials/rss.html').read()


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

class settings:
    def GET(self):
        goog = users.get_current_user()
        if not goog:
            return web.seeother(users.create_login_url('/settings'))

        user = db.GqlQuery("SELECT * FROM User WHERE goog = :1", goog).get()
        if not user:
            return render_no_layout.settings()
        else:
            return render_no_layout.thanks()


    def POST(self):
        user = db.GqlQuery("SELECT * FROM User WHERE goog = :1", users.get_current_user()).get()
        if not user:
            user = User()
            user.goog = users.get_current_user()
            user.name = web.input().name
            user.put() # FIXME: uniq on name

        return render_no_layout.thanks()

# redirects
# pages
# articles ? (draft)
# forums

class welcome:
    def GET(self):
        user = db.GqlQuery("SELECT * FROM User WHERE goog = :1", users.get_current_user()).get()
        if not user:
            return render.welcome()
        else:
            return web.seeother('/update')

    def POST(self):
        user = db.GqlQuery("SELECT * FROM User WHERE goog = :1", users.get_current_user()).get()
        if not user:
            user = User()
            user.goog = users.get_current_user()
            user.name = web.input().name
            user.put() # FIXME: uniq on name

        return web.seeother('/')

class profile:
    def GET(self, key):
        profile = Profile.get(key)
        if profile:
            return render.profile(profile)
        else:
            return web.seeother('/')


class forum:
    def GET(self):
        forums = db.GqlQuery("SELECT * FROM Forum order by name")
        return render.forums(forums, users)

class forum_feed:
    def GET(self):
        posts = db.GqlQuery("SELECT * FROM Post order by created desc")
        web.header('Content-Type', 'text/xml')
        return render_no_layout.forum_feed(posts, base=None)


class topics:
    def GET(self, slug):
        key = db.Key.from_path('Forum', slug)
        forum = Forum.get(key)
        if forum:
            return render.forumTopics(forum)
        else:
            if users.is_current_user_admin():
                return render.forumEdit(slug)

    def POST(self, slug):
        if not users.is_current_user_admin():
            return web.seeother("/")

        forum = Forum(key_name=slug)
        i = web.input()
        forum.slug = slug
        forum.name = i.name
        forum.description = i.description
        forum.put()
        return web.seeother("%s/forum" % slug)

class newTopic:
    def GET(self, slug):
        user = users.get_current_user()
        if user:
            key = db.Key.from_path('Forum', slug)
            forum = Forum.get(key)
            if forum:
                return render.forumNewTopic(forum)
        else:
            return web.seeother(users.create_login_url('%s/forum/new' % slug))
    def POST(self, slug):
        key = db.Key.from_path('Forum', slug)
        forum = Forum.get(key)
        if not forum:
            return render.seeother('/')

        i = web.input()

        topic = Topic()
        topic.forum = forum
        topic.title = i.title
        topic.user = users.get_current_user()

        topic.put()
        post = Post()
        post.topic = topic
        post.body = i.body
        post.body_html = sanitize.html(i.body)
        post.user = users.get_current_user()
        post.put()
        return web.seeother("%s/forum/%s" % (slug, topic.key()))

class topic:
    def GET(self, slug, key):
        forum = Forum.get(db.Key.from_path('Forum', slug))
        topic = Topic.get(key)
        user = users.get_current_user()

        if user:
            login_url = None
            gravatar = "http://www.gravatar.com/avatar.php?"
            gravatar += urllib.urlencode({'gravatar_id':hashlib.md5(user.email().lower()).hexdigest(), 'size':str(48), 'default':'identicon'})

        else:
            gravatar = None
            login_url = users.create_login_url('%s/forum/%s' % (slug, key))
        return render.topic(topic, login_url, gravatar)

    def POST(self, slug, key):
        i = web.input()

        topic = Topic.get(key)
        post = Post()
        post.topic = topic
        post.body = i.body
        post.body_html = sanitize.html(i.body)
        post.user = users.get_current_user()
        post.put()
        if post.is_saved():
            topic.last_post = post.created
            topic.put()
        return web.seeother("%s/forum/%s" % (slug, topic.key()))


class page:
    def GET(self, slug):
        key = db.Key.from_path('Redirect', slug)
        redirect = Redirect.get(key)
        if redirect:
            return web.seeother(redirect.url)
        key = db.Key.from_path('Page', slug)
        page = Page.get(key)
        if users.is_current_user_admin():
            if page:
                if web.ctx.query == '':
                    return render.pageShow(page, slug)
            else:
                page = Page()
            return render.pageEdit(page, slug)
        else:
            if page:
                return render.pageShow(page, slug)
            web.ctx.status = '404 shit happens'
            return render.missing(slug)

    def POST(self, slug):
        if not users.is_current_user_admin():
            return web.seeother('/')
        key = db.Key.from_path('Page', slug)
        page = Page.get(key)
        if not page:
            page = Page(key_name=slug)

        i = web.input()
        page.slug = slug
        page.title = i.title
        page.body = i.body
        page.metaDescription = i.metaDescription
        page.put()
        return web.seeother(slug)

class user:
    def GET(self, name):
        user = db.GqlQuery("SELECT * FROM User WHERE name = :1", name).get()
        return render.user(user)

class extensions:
    def GET(self):
        extensions = db.GqlQuery("SELECT * FROM Extension ORDER BY name ASC")
        return render.extensions(extensions)

class extension:
    def GET(self, mid,):
        extension = db.GqlQuery("SELECT * FROM Extension WHERE mid = :1", mid)[0]
        return render.extension(extension)

def getUser():
    goog = users.get_current_user()
    if goog:
        return db.GqlQuery("SELECT * FROM User WHERE goog = :1", goog).get()

class update:
    def GET(self):
        user = getUser()
        if not user:
            return web.seeother('/login')

        return render.user(user)

    def POST(self, key=None):
        web.debug("hi")
        json = simplejson.loads(web.input().data)

        if key and key != '':
            send_welcome = False
            profile = Profile.get(db.Key.from_path('Profile', key))
            # FIXME: check if signature matches
            # web.ctx.status = "401 Unauthorized"
            # return

        else:
            send_welcome = True
            secret_uuid = uuid.uuid4()
            profile = Profile(secret=secret_uuid.hex)
            # FIXME: return the key/secret on success

        profile.version = json['system']['version']
        profile.os = json['system']['OS']
        profile.platform = json['system']['name']
        profile.put()

        web.debug("profile: %s" % profile)

        # Build a dictionary of the current extensions
        profile_extensions = profile.profileextension_set.fetch(100)

        px_dict = {}
        for e in profile_extensions:
            px_dict[e.extension.mid] = e
        web.debug(px_dict)

        local_extensions = json['extensions']
        for mid in local_extensions:
            local_extension = local_extensions[mid]
            web.debug("processing " + mid)
            key = db.Key.from_path('Extension', mid)
            extension = Extension.get(key)
            if not extension:
                web.debug("new extension: " + mid)
                extension = Extension(key_name=mid)
                extension.mid = mid
                extension.name = local_extension['name']
                extension.updateRDF = local_extension['updateRDF']
                extension.description = local_extension['description']
                extension.creator = local_extension['creator']
                extension.homepageURL = local_extension['homepageURL']
                extension.developers = local_extension['developers']
                extension.translators = local_extension['translators']
                extension.contributors = local_extension['contributors']
                extension.put()
            if px_dict.has_key(mid):
                web.debug("user had extension " + mid)
                px_dict[mid].version = local_extension['version']
                px_dict[mid].put()
                del px_dict[mid]
            else:
                web.debug("user did not have extension " + mid)
                px = ProfileExtension()
                px.extension = extension
                px.version = local_extension['version']
                px.profile = profile
                px.put()

        # Delete any user extensions from the database that weren't in the update
        for px in px_dict:
            web.debug("user no longer has extension " + mid)
            px_dict[px].delete()

        web.debug("profile key: %s" % profile.key())

        web.ctx.status = "200 OK"
        if send_welcome:
            web.header('Content-Type', 'text/x-json')
            return simplejson.dumps({'profile': str(profile.key()), 'secret': profile.secret })
        else:
            return


class redirect:
    def GET(self, slug):
        web.Redirect(slug)

class articleRedirect:
    def GET(self, slug):
        web.Redirect('/articles/'+slug)

app = web.application(urls, globals())
main = app.cgirun()

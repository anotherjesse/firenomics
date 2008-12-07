from google.appengine.api import users
from vendor.recaptcha.client import captcha
from vendor import web

from models import *

PUB = 'FIXME'

urls = (
  '(.*).html$', 'rewrite',
  '/', 'index',
  '/about', 'about',
  '/articles', 'list',
  '/articles/([A-Za-z0-9\-]+)', 'show',
  '/tags/([A-Za-z0-9\-]+)', 'tag',
  '/articles/\d+/\d+/\d+/([A-Za-z0-9\-]+)', 'redirect'
)

render = web.template.render('templates/main', base='../base')

web.template.Template.globals['card'] = open('templates/partials/card.html').read()
web.template.Template.globals['rss'] = open('templates/partials/rss.html').read()

class rewrite:
    def GET(self, slug):
        web.Redirect(slug)

class index:
    def GET(self):
        articles = db.GqlQuery("SELECT * FROM Article ORDER BY created DESC LIMIT 10")
        return render.index(articles)

class show:
    def GET(self, slug):
        admin = users.is_current_user_admin()
        articles = db.GqlQuery("SELECT * FROM Article WHERE slug = :1", slug)
        article = articles.get()
        captcha_html = captcha.displayhtml(PUB)
        return render.article(article, captcha_html, admin)

class tag:
    def GET(self, tag):
        articles = db.GqlQuery("SELECT * FROM Article WHERE tags = :1 ORDER BY created", tag)
        return render.tagged(articles, tag)

class list:
    def GET(self):
        articles = db.GqlQuery("SELECT * FROM Article ORDER BY created DESC")
        return render.articles(articles)

class about:
    def GET(self):
        return render.about()

class redirect:
    def GET(self, slug):
        web.Redirect('/articles/'+slug)

app = web.application(urls, globals())
main = app.cgirun()

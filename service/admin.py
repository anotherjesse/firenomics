import urllib, hashlib, datetime, string
from vendor import web
import simplejson
from os import path
from google.appengine.ext import db
from google.appengine.api import urlfetch
from models import *
from utils import *
import sanitize


urls = (
  '/admin', 'index',
  '/admin/fix', 'fix',
  '/admin/articles', 'articles',
  '/admin/articles/([A-Za-z0-9\-]+)', 'edit_article',
  '/admin/redirect(/.*)', 'redirect',
  '/admin/comments/([A-Za-z0-9]+)', 'edit_comment',
  '/admin/comments/delete/([A-Za-z0-9]+)', 'delete_comment'
)

render = web.template.render('templates/admin/', base='../base')
web.template.Template.globals['hack'] = Article
web.template.Template.globals['analytics'] = analytics

class index:
    def GET(self):
        articles  = Article.all().order('-created').fetch(limit=20)
        comments  = Comment.all().order('-created').fetch(limit=20)
        pages     = Page.all().order('-created').fetch(limit=20)
        redirects = Redirect.all().fetch(limit=20)
        return render.index(articles, comments, pages, redirects)


class fix:
    def GET(self):
        offset = int(web.input().offset)
        comments = Comment.all().fetch(limit=40, offset=offset)
        for comment in comments:
            comment.body_html = sanitize.html(comment.body)
            comment.put()
        cnt = Comment.all().count()
        if offset + 40 < cnt:
            return "<a href='/admin/fix?offset=%s'>next</a>" % (offset + 40)
        else:
            return "done"

class redirect:
    def GET(self, slug):
        key = db.Key.from_path('Redirect', slug)
        item = Redirect.get(key)
        if not item: item = Redirect()
        return render.redirect(item, slug)
    def POST(self, slug):
        key = db.Key.from_path('Redirect', slug)
        item = Redirect.get(key)
        if not item: item = Redirect(key_name=slug)
        i = web.input()
        item.url = i.url
        item.slug = slug
        item.put()
        return web.seeother('/admin')

class articles:
    def GET(self):
        article = Article()
        return render.article(article)
    def POST(self):
        i = web.input()
        article = Article()
        article.title = i.title
        article.slug = i.slug
        article.body = i.body
        # article.created = datetime.datetime.strptime(i.created.split('.')[0], '%Y-%m-%d %H:%M:%S')
        article.tags = [x.strip() for x in i.tags.split(',')]
        article.put()
        return web.seeother('/articles/'+article.slug)

class edit_article:
    def GET(self, slug):
        articles = db.GqlQuery("SELECT * FROM Article WHERE slug = :1", slug)
        article = articles.get()
        return render.article(article)
    def POST(self, slug):
        i = web.input()
        articles = db.GqlQuery("SELECT * FROM Article WHERE slug = :1", slug)
        article = articles.get()
        article.title = i.title
        article.slug = i.slug
        article.body = i.body
        article.created = datetime.datetime.strptime(i.created.split('.')[0], '%Y-%m-%d %H:%M:%S')
        article.tags = [x.strip() for x in i.tags.split(',')]
        article.put()
        return web.seeother('/articles/'+article.slug)

class edit_comment:
    def GET(self, key):
        comment = Comment.get(key)
        return render.comment(comment)
    def POST(self, key):
        i = web.input()
        comment = Comment.get(key)
        comment.name = i.name
        comment.body = i.body
        comment.body_html = sanitize.html(i.body)
        comment.url = i.url
        comment.put()
        return web.seeother('/articles/'+comment.article.slug)

class delete_comment:
    def GET(self, key):
        comment = Comment.get(key)
        article = comment.article
        comment.delete()
        return web.seeother('/articles/'+article.slug)

app = web.application(urls, globals())
main = app.cgirun()

import urllib, hashlib, datetime
from vendor import web
from os import path
from google.appengine.ext import db
from models import *
from vendor.recaptcha.client import captcha
import sanitize

#PUB  = 'xxx'
#PRIV = 'xxx'

render = web.template.render('templates/main', base='../base')

urls = (
  '/comment', 'comment'
)

class comment():
    def POST(self):
        i = web.input()
        slug = i.slug
        articles = db.GqlQuery("SELECT * FROM Article WHERE slug = :1", slug)
        article = articles.get()

        #result = captcha.submit(i.recaptcha_challenge_field, i.recaptcha_response_field, PRIV, web.ctx['ip'])
        #if not result.is_valid:
        #    return render.captcha()

        comment = Comment()
        comment.article = article
        comment.name = i.name
        comment.email = i.email
        comment.body = i.body
        # comment.created = datetime.datetime.strptime(i.created.split('.')[0], '%Y-%m-%d %H:%M:%S')
        comment.body_html = sanitize.html(i.body)
        comment.url = sanitize.url(i.url)
        comment.raw = web.data()
        comment.put()
        return web.seeother('/articles/'+article.slug)

app = web.application(urls, globals())
main = app.cgirun()

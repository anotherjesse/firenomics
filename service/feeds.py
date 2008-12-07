from google.appengine.ext import db
from models import *
from vendor import web
import datetime

render = web.template.render('templates/main')

urls = (
  '(.*)', 'feed'
)

class feed:
    def GET(self, path):
        if path == '/xml/comments':
            comments = db.GqlQuery("SELECT * FROM Comment ORDER BY created DESC LIMIT 20")
            web.header('Content-Type', 'application/rss+xml')
            return render.comments(comments)
        else:
            if web.ctx.env.get('HTTP_USER_AGENT',"").find("FeedBurner") == -1:
                return web.Redirect("http://feeds.feedburner.com/overstimulate")

            articles = db.GqlQuery("SELECT * FROM Article WHERE created > :1 ORDER BY created DESC LIMIT 10", datetime.datetime(2008, 04, 25))
            web.header('Content-Type', 'application/rss+xml')
            return render.feed(articles)

app = web.application(urls, globals())
main = app.cgirun()

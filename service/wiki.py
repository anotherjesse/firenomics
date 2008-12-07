import urllib, hashlib, datetime
from vendor import web
from models import *

urls = (
  '/wiki', 'index',
  '/wiki/e/(.*)', 'edit',
  '/wiki/v/(.*)', 'version',
  '/wiki/(.*)', 'show'
)

render = web.template.render('templates/wiki', base='../base')

class show:
    def GET(self, name):
        page = db.GqlQuery("SELECT * FROM Page WHERE name = :1", name).get()
        if page:
            versions = page.pageversion_set.order('-created').fetch(10,1)
            more_versions = len(versions) == 10
            versions = versions[:9]
            return render.show(page, versions, more_versions)
        else:
            return web.seeother('/wiki/e/'+name)

class version:
    def GET(self, key):
        version = PageVersion.get(key)
        return render.history(version)

class edit:
    def GET(self, name):
        page = db.GqlQuery("SELECT * FROM Page WHERE name = :1", name).get()
        if not page:
            page = Page(name=name)
        return render.edit(page)
    def POST(self, name):
        page = db.GqlQuery("SELECT * FROM Page WHERE name = :1", name).get()
        if not page:
            page = Page(name=name)
        page.body = web.input().body
        page.updated = datetime.datetime.now()
        page.put()
        PageVersion(page=page, body=page.body).put()
        return web.seeother('/wiki/'+page.name)

app = web.application(urls, globals())
main = app.cgirun()

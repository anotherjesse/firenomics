from google.appengine.ext import db
from google.appengine.api import users
from vendor import web
from models import *

import simplejson, uuid, md5, re

urls = (
  '/api/v1/recommend/(.*)', 'recommend',
  '/api/v1/update', 'update',
  '/api/v1/update/(.*)', 'update'
)


class recommend:
    def POST(self, mid):
        extension = db.GqlQuery("SELECT * FROM Extension WHERE mid = :1", mid)[0]
        for rec in extension.extensionrecommendation_set.fetch(100):
            rec.delete()

        added = 0

        for mid in web.input().recommended.split("/"):
            recommended = db.GqlQuery("SELECT * FROM Extension WHERE mid = :1", mid)[0]
            er = ExtensionRecommendation(recommended=recommended, extension=extension)
            er.put()
            added += 1

        return "Extension: %s now has %s recommendations" % (extension.name, added)


class update:
    def POST(self, key=None):
        web.debug("hi: %s" % key)
        send_welcome = False
        json = simplejson.loads(web.input().data)

        if key and key != '':
            profile = Profile.get(key)

            if profile:
                sig = web.input().sig
                data = web.data()
                expected = md5.new(data + profile.secret).hexdigest()
                if sig != expected:
                    web.ctx.status = "401 Unauthorized"
                    return "Invalid Signature"
            else:
                send_welcome = 410

        else:
            send_welcome = 200

        if send_welcome:
            secret_uuid = uuid.uuid4()
            profile = Profile(secret=secret_uuid.hex)

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

        if send_welcome:
            web.ctx.status = "%s New Profile" % send_welcome
            web.header('Content-Type', 'text/x-json')
            return simplejson.dumps({'profile': str(profile.key()), 'secret': profile.secret})
        else:
            web.ctx.status = "200 OK"
            return "KTHXBAI"


app = web.application(urls, globals())
main = app.cgirun()

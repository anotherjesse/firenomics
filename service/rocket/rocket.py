# Copyright 2008 Kaspars Dancis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import logging, base64
from datetime import datetime

from google.appengine.api import datastore, datastore_admin, datastore_types, datastore_errors

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache

from rocket.consts import *
from rocket.config import SECRET_KEY

from rocket import utils



class Rocket(webapp.RequestHandler):
    def get(self):
        path = self.request.path.split("/")

        self.response.headers['Content-Type'] = 'text/xml'

        if self.request.get("secret_key") !=  SECRET_KEY:
            self.response.out.write(u'<error>Unauthorized</error>\n')
            return

        if len(path) < 3 or path[2] == '':
            self.response.out.write(u'<error>Please specify an entity kind</error>\n')
            return

        kind = path[2]

        self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n')
        self.response.out.write(u'<updates>\n')

        query = datastore.Query(kind)

        timestamp_field = self.request.get("timestamp")
        if not timestamp_field:
            timestamp_field = DEFAULT_TIMESTAMP_FIELD

        batch_size = self.request.get("count")
        if not batch_size:
            batch_size = DEFAULT_BATCH_SIZE
        else:
            batch_size = int(batch_size)

        f = self.request.get("from")
        if f:
            query['%s >' % timestamp_field] = utils.from_iso(f)

        query.Order(timestamp_field)

        entities = query.Get(batch_size, 0)

        for entity in entities:
            self.response.out.write(u'    <%s key="%s">\n' % (kind, ae_to_rocket(TYPE_KEY, entity.key())))

            for field, value in entity.items():
                if isinstance(value, list):
                    if len(value) > 0 and value[0] != None:
                        field_type = get_type(value[0])
                        self.response.out.write(u'        <%s type="%s" list="true">\n' % (field, field_type))
                        for item in value:
                            self.response.out.write(u"            <item>%s</item>\n" % ae_to_rocket(field_type, item))
                        self.response.out.write(u'</%s>\n' % field)
                else:
                    if value != None:
                        if field == timestamp_field:
                            field_type = TYPE_TIMESTAMP
                        else:
                            field_type = get_type(value)

                        self.response.out.write(u'        <%s type="%s">%s</%s>\n' % (field, field_type, ae_to_rocket(field_type, value), field))

            self.response.out.write(u'    </%s>\n' % kind)

        self.response.out.write(u'</updates>')


    def post(self):
        path = self.request.path.split("/")

        self.response.headers['Content-Type'] = 'text/plain'

        if len(path) < 3 or path[2] == '':
            self.response.out.write(u'Please specify an entity kind\n')
            return

        kind = path[2]

        entity = None
        clear_cache = False

        key_name_or_id = self.request.get(TYPE_KEY)
        if key_name_or_id:
            if key_name_or_id[0] in "0123456789":
                key = datastore.Key.from_path(kind, int(key_name_or_id)) # KEY ID
            else:
                key = datastore.Key.from_path(kind, key_name_or_id) # KEY NAME

            try: entity = datastore.Get(key)
            except datastore_errors.EntityNotFoundError: pass

        if not entity:
            if key_name_or_id:

                if key_name_or_id[0] in "0123456789":
                    self.response.out.write(u'Entity with AppEngine ID=%s is not found.\n' % key_name_or_id)
                    return

                entity = datastore.Entity(kind=kind,name=key_name_or_id)
            else:
                entity = datastore.Entity(kind=kind)
        else:
            clear_cache = True

        args = self.request.arguments()
        for arg in args:
            if arg != TYPE_KEY:
                bar = arg.find('|')
                if bar > 0:
                    field_type = arg[:bar]
                    field_name = arg[bar + 1:]
                    value = self.request.get(arg)
                    if field_type.startswith("*"):
                        field_type = field_type[1]
                        if len(value) == 0:
                            if entity.has_key(field_name):
                                del entity[field_name]
                        else:
                            entity[field_name] = map(lambda v: rocket_to_ae(field_type, v), value.split('|'))
                    else:
                        entity[field_name] = rocket_to_ae(field_type, value)


        datastore.Put(entity)

        if clear_cache:
            # very simplistic measure for ensuring an old version of updated entity is cached
            # assumes that cache key = entity key name
            memcache.delete(key_name_or_id)

        self.response.out.write(u'OK')




def get_type(value):
    if isinstance(value, datetime):
        return TYPE_DATETIME
    elif isinstance(value, bool):
        return TYPE_BOOL
    elif isinstance(value, long):
        return TYPE_LONG
    elif isinstance(value, float):
        return TYPE_FLOAT
    elif isinstance(value, int):
        return TYPE_INT
    elif isinstance(value, datastore_types.Text):
        return TYPE_TEXT
    elif isinstance(value, datastore_types.Key):
        return TYPE_REFERENCE
    elif isinstance(value, datastore_types.Blob):
        return TYPE_BLOB
    else:
        return TYPE_STR

    return None



def ae_to_rocket(field_type, ae_value):
    if ae_value == None:
        rocket_value = ""
    elif field_type == TYPE_DATETIME or field_type == TYPE_TIMESTAMP:
        rocket_value = utils.to_iso(ae_value)
    elif field_type == TYPE_REFERENCE:
        rocket_value = "%s/%s" % (ae_value.kind(), ae_to_rocket(TYPE_KEY, ae_value))
    elif field_type == TYPE_KEY:
        if ae_value.name():
            rocket_value = utils.escape(ae_value.name())
        else:
            rocket_value = "%d" % ae_value.id()
    elif field_type == TYPE_BOOL:
        rocket_value = "%d" % ae_value
    elif field_type == TYPE_BLOB:
        rocket_value = base64.b64encode(ae_value)
    else:
        rocket_value = utils.escape(u"%s" % ae_value)

    return rocket_value



def rocket_to_ae(field_type, rocket_value):
    if not rocket_value:
        ae_value = None
    elif field_type == TYPE_DATETIME or field_type == TYPE_TIMESTAMP:
        ae_value = utils.from_iso(rocket_value)
    elif field_type == TYPE_BOOL:
        ae_value = bool(int(rocket_value))
    elif field_type == TYPE_LONG:
        ae_value = long(rocket_value)
    elif field_type == TYPE_FLOAT:
        ae_value = float(rocket_value)
    elif field_type == TYPE_INT:
        ae_value = int(rocket_value)
    elif field_type == TYPE_TEXT:
        ae_value = datastore_types.Text(rocket_value.replace('&#124;','|'))
    elif field_type == TYPE_REFERENCE:
        slash = rocket_value.find("/")
        if slash > 0:
            kind = rocket_value[:slash]
            key_name_or_id = rocket_value[slash + 1:]
            if key_name_or_id[0] in "0123456789":
                key_name_or_id = int(key_name_or_id)
            ae_value = datastore.Key.from_path(kind, key_name_or_id)
        else:
            logging.error("invalid reference value: %s" % rocket_value)
            ae_value = None
    elif field_type == TYPE_BLOB:
        ae_value = datastore_types.Blob(base64.b64decode(rocket_value))
    else: #str
        ae_value = (u"%s" % rocket_value).replace('&#124;','|')

    return ae_value



application = webapp.WSGIApplication([('/rocket/.*', Rocket)], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

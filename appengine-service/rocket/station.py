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

import urllib, logging, os, sys, traceback, time, base64
from datetime import timedelta, datetime
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError
from sys import stdout

import MySQLdb as db

from consts import *

import_config = "from config import *"

if __name__ == "__main__":
    daemon = False
    in_loop = False

    for arg in sys.argv[1:]:
        if arg == "-d":
            daemon = True
        elif arg == "-l":
            in_loop = True
        elif arg.startswith("-c="):
            if arg.endswith(".py"):
                config = arg[3:len(arg)-3]
            else:
                config = arg[3:]

            import_config = "from %s import *" % config
        else:
            print "Usage: station.py [-d|-l] [-c=config file]"
            print '-d: run in daemon mode (*nix platforms only)'
            print '-l: run in loop mode'
            print '-c: configuration file, by default "config"'
            sys.exit()

exec import_config

import utils

send_states = {}
receive_states = {}
tables = {}
con = None

def connect():
    global con

    kwargs = {
        'charset': 'utf8',
        'use_unicode': True,

    }

    if DATABASE_USER:
        kwargs['user'] = DATABASE_USER
    if DATABASE_NAME:
        kwargs['db'] = DATABASE_NAME
    if DATABASE_PASSWORD:
        kwargs['passwd'] = DATABASE_PASSWORD
    if DATABASE_HOST.startswith('/'):
        kwargs['unix_socket'] = DATABASE_HOST
    elif DATABASE_HOST:
        kwargs['host'] = DATABASE_HOST
    if DATABASE_PORT:
        kwargs['port'] = int(DATABASE_PORT)

    con = db.connect(**kwargs)



def read_send_receive_states():
    cur = con.cursor()

    cur.execute('show tables like "rocket_station"')

    if cur.fetchone():
        cur.execute("select kind, send_state, receive_state from rocket_station")
        for row in cur.fetchall():
            send_states[row[0]] = row[1]
            receive_states[row[0]] = row[2]
    else:
        cur.execute("CREATE TABLE rocket_station (kind VARCHAR(255), send_state VARCHAR(500), receive_state VARCHAR(500), PRIMARY KEY (kind)) ENGINE = %s CHARACTER SET utf8 COLLATE utf8_general_ci" % DATABASE_ENGINE)

    con.commit()

    cur.close()



def write_send_state(cur, kind, send_state):
    if send_states.has_key(kind) or receive_states.has_key(kind):
        cur.execute("""UPDATE rocket_station SET send_state =  %s WHERE kind = %s""", (send_state, kind))
    else:
        cur.execute("""INSERT INTO rocket_station (kind, send_state) VALUES (%s, %s)""", (kind, send_state))



def write_receive_state(cur, kind, receive_state):
    if send_states.has_key(kind) or receive_states.has_key(kind):
        cur.execute("""UPDATE rocket_station SET receive_state =  %s WHERE kind = %s""", (receive_state, kind))
    else:
        cur.execute("""INSERT INTO rocket_station (kind, receive_state) VALUES (%s, %s)""", (kind, receive_state))



def replicate_all():
    updates = False

    for kind, options in ROCKET_ENTITIES.items():
        if replicate(kind, options):
            updates = True

    return updates


def replicate(kind, options):
    updates = False

    if options.has_key(TABLE_NAME): table_name = options[TABLE_NAME]
    else: table_name = kind

    if options.has_key(TIMESTAMP_FIELD): timestamp_field = options[TIMESTAMP_FIELD]
    else: timestamp_field = DEFAULT_TIMESTAMP_FIELD

    if options.has_key(TABLE_KEY_FIELD): table_key_field = options[TABLE_KEY_FIELD]
    else: table_key_field = DEFAULT_KEY_FIELD

    if options.has_key(TABLE_KEY_FIELD): table_key_field = options[TABLE_KEY_FIELD]
    else: table_key_field = DEFAULT_KEY_FIELD

    if options.has_key(SEND_FIELDS): send_fields = set(options[SEND_FIELDS])
    else: send_fields = None

    if options.has_key(RECEIVE_FIELDS): receive_fields = set(options[RECEIVE_FIELDS])
    else: receive_fields = None

    if options.has_key(EMBEDDED_LIST_FIELDS): embedded_list_fields = set(options[EMBEDDED_LIST_FIELDS])
    else: embedded_list_fields = []

    if options.has_key(MODE): mode = options[MODE]
    else: mode = SEND_RECEIVE

    if mode == SEND_RECEIVE or mode == SEND:
        if send_updates(kind, table_name, timestamp_field, table_key_field, send_fields, embedded_list_fields):
            updates = True

    if mode == RECEIVE_SEND or mode == SEND_RECEIVE or mode == RECEIVE:
        if receive_updates(kind, table_name, timestamp_field, table_key_field, receive_fields, embedded_list_fields):
            updates = True

    if mode == RECEIVE_SEND:
        if send_updates(kind, table_name, timestamp_field, table_key_field, send_fields, embedded_list_fields):
            updates = True

    return updates


def send_updates(kind, table_name, timestamp_field, table_key_field, send_fields, embedded_list_fields):
    cur = con.cursor()

    table = get_table_metadata(cur, table_name, timestamp_field, table_key_field, embedded_list_fields)

    if not table.fields.has_key(timestamp_field):
        logging.error('Error: table %s is missing timestamp field "%s"' % (table_name, timestamp_field))
        return

    if not table.fields.has_key(table_key_field):
        logging.error('Error: table %s is missing key field "%s"' % (table_name, table_key_field))
        return

    cur.execute("select current_timestamp")
    to_timestamp = cur.fetchone()[0] - timedelta(seconds=1) # -1 second to ensure there will be no more updates with that timestamp
    params = [to_timestamp]

    sql = "select %s from %s where %s < " % (', '.join(table.fields.keys()), table_name, timestamp_field) + """%s """
    if send_states.has_key(kind) and send_states[kind]:
        sql += "and " + timestamp_field + """ > %s """
        params.append(utils.from_iso(send_states[kind]))
        logging.info("send %s: from %s" % (kind, send_states[kind]))
    else:
        logging.info("send %s: from beginning" % (kind))

    sql += "order by %s " % timestamp_field

    offset = 0
    count = BATCH_SIZE
    while count == BATCH_SIZE:
        count = 0
        batch_sql = sql + " limit %d, %d" % (offset, BATCH_SIZE)
        cur.execute(batch_sql, params)
        intermediate_timestamp = None
        for row in cur.fetchall():
            count += 1

            key = None

            entity = {
            }

            i = 0
            for field_name, field_type in table.fields.items():

                field_value = row[i]

                if field_name == timestamp_field and field_value:
                    intermediate_timestamp = field_value - timedelta(seconds=1)
                    # do not send time stamp to avoid send/receive loop

                elif field_name == table_key_field:
                    key = field_value
                    entity[TYPE_KEY] = mysql_to_rocket(TYPE_KEY, field_value)

                elif field_type == TYPE_STR_LIST:
                    entity["*%s|%s" % (TYPE_STR, field_name)] = mysql_to_rocket(TYPE_STR, field_value)

                else:
                    if field_name.endswith("_ref"):
                        field_name = field_name[:len(field_name)-4]

                    if not send_fields or field_name in send_fields:
                        entity["%s|%s" % (field_type, field_name)] = mysql_to_rocket(field_type, field_value)

                i += 1


            if not key:
                logging.error('send %s: key field %s is empty' % (kind, table_key_field))
                continue

            # retrieve lists
            for field_name, field_type in table.list_fields.items():
                if not send_fields or field_name in send_fields:
                    cur.execute('select %s from %s_%s where %s = ' % (field_name, table_name, field_name, table_key_field) + """%s""", (key))

                    items = []
                    for item in cur.fetchall():
                        items.append(mysql_to_rocket(field_type, item[0]))

                    entity["*%s|%s" % (field_type, field_name)] = '|'.join(items)

            logging.debug('send %s: key=%s' % (kind, key))

            for attempt in range(3): # try three times
                try:
                    send_row(kind, key, entity)
                    break
                except:
                    logging.exception('send %s: key=%s, attempt #%d failed' % (kind, key, attempt + 1))
            else:
                # if all retries failed - rollback and return
                con.rollback()
                return

        logging.info('send %s: batch end, count=%d, offset=%d' % (kind, count, offset))
        offset += count

        if intermediate_timestamp:
            intermediate_timestamp = utils.to_iso(intermediate_timestamp)
            write_send_state(cur, kind, intermediate_timestamp)
            con.commit()
            send_states[kind] = intermediate_timestamp

    to_timestamp = utils.to_iso(to_timestamp)
    write_send_state(cur, kind, to_timestamp)
    con.commit()
    send_states[kind] = to_timestamp

    cur.close()

    return count > 0 or offset > 0



def send_row(kind, key, entity):
    result = urllib.urlopen("%s/%s?secret_key=%s" % (ROCKET_URL, kind, SECRET_KEY), urllib.urlencode(entity))
    try:
        response = ''.join(result).strip(" \r\n")
        if response != "OK":
            logging.error(response)
    finally:
        result.close()



def receive_updates(kind, table_name, timestamp_field, table_key_field, receive_fields, embedded_list_fields):
    updates = False

    # receive updates
    count = BATCH_SIZE
    while count == BATCH_SIZE:
        count = 0

        url = "%s/%s?secret_key=%s&timestamp=%s&count=%d" % (ROCKET_URL, kind, SECRET_KEY, timestamp_field, BATCH_SIZE)
        if receive_states.has_key(kind) and receive_states[kind]:
            url += "&from=%s" % receive_states[kind]
            logging.info("receive %s: from %s" % (kind, receive_states[kind]))
        else:
            logging.info("receive %s: from beginning" % (kind))

        result = urllib.urlopen(url)
        response = ''.join(result)

        cur = con.cursor()

        try:

            xml = ElementTree.XML(response)
            for entity in xml:
                receive_row(cur, kind, table_name, timestamp_field, table_key_field, receive_fields, embedded_list_fields, entity)
                count += 1
                last_timestamp = entity.findtext("timestamp")

            if count > 0:
                updates = True
                write_receive_state(cur, kind, last_timestamp)
                con.commit()
                receive_states[kind] = last_timestamp

        except ExpatError, e:
            logging.exception("receive %s: error parsing response: %s, response:\n%s" % (kind, e, response))
            con.rollback()

        except:
            logging.exception("receive %s: error" % kind)
            con.rollback()

        cur.close()

        logging.info("receive %s: batch end, count=%d" % (kind, count))

    return updates




def receive_row(cur, kind, table_name, timestamp_field, table_key_field, receive_fields, embedded_list_fields, entity):
    fields = []
    values = []

    table = get_table_metadata(cur, table_name, timestamp_field, table_key_field, embedded_list_fields)

    key = rocket_to_mysql(TYPE_KEY, entity.attrib[TYPE_KEY])

    logging.debug("receive %s: key=%s" % (kind, key))

    row = None

    for field in entity:
        field_name = field.tag

        if not receive_fields or field_name in receive_fields:
            # only receive fields if no receive fields are specified (means ALL will be received
            # or the field is in receive fields list

            field_type = field.attrib["type"]

            if field_type == TYPE_REFERENCE:
                field_name += "_ref"

            is_list = field.attrib.has_key("list")
            is_embedded_list = field_name in embedded_list_fields
            synchronize_field(cur, table, field_name, field_type, is_list, is_embedded_list)

            if is_embedded_list:
                list_values = []
                for item in field:
                    list_values.append(item.text)
                fields.append("`%s`" % field_name)
                values.append('|'.join(list_values))
            elif is_list:
                list_table_name = '%s_%s' % (table_name, field_name)
                sql = 'DELETE FROM ' + list_table_name + ' WHERE ' +  table_key_field + """ = %s"""
                cur.execute(sql, (key))
                for item in field:
                    sql = 'INSERT INTO ' + list_table_name + ' (' + table_key_field + ',' + field_name + """) VALUES (%s, %s)"""
                    cur.execute(sql, (key, rocket_to_mysql(field_type, item.text)))
            else:
                fields.append("`%s`" % field_name)
                values.append(rocket_to_mysql(field_type, field.text))

    cur.execute("SELECT * FROM " + table_name + " WHERE " + table_key_field + """ = %s""", (key))
    if cur.fetchone():
        # record already exist
        if len(fields) > 0:
            values.append(key)
            sql = 'UPDATE `%s` SET %s WHERE %s = ' % (table_name, ','.join(map(lambda f: f + """=%s""", fields)), table_key_field) + """%s"""
            cur.execute(sql, values)

    else:
        fields.append(table_key_field)
        values.append(key)
        sql = 'INSERT INTO `%s` (%s) VALUES (%s)' % (table_name, ','.join(fields), ','.join(map(lambda f: """%s""", fields)))
        cur.execute(sql, values)




def get_table_metadata(cur, table_name, timestamp_field, table_key_field, embedded_list_fields):
    global tables

    if tables.has_key(table_name):
        table = tables[table_name]
        return table
    else:
        cur.execute('SHOW TABLES LIKE "%s"' % table_name)
        if cur.fetchone():
            # table exist

            # start with empty definition
            table = Table(table_name, timestamp_field, table_key_field)

            # add table fields
            cur.execute('SHOW COLUMNS FROM %s' % table_name)
            for col in cur.fetchall():
                field_name = col[0]
                if field_name in embedded_list_fields:
                    table.fields[field_name] = TYPE_STR_LIST # for embedded lists currently we only support string values
                else:
                    field_type = normalize_type(field_name, col[1])
                    table.fields[field_name] = field_type

            # add list fields stored in separate tables (TableName_ListField)
            cur.execute('SHOW TABLES LIKE "%s_%%"' % table_name)
            for row in cur.fetchall():
                list_table_name = row[0]
                list_field_name = list_table_name[len(table_name) + 1:]
                cur.execute('SHOW COLUMNS FROM %s' % list_table_name)
                for col in cur.fetchall():
                    field_name = col[0]
                    if field_name == list_field_name:
                        field_type = normalize_type(field_name, col[1])
                        table.list_fields[field_name] = field_type
                        break

            tables[table_name] = table

            return table

        else:
            # tables is missing
            cur.execute("CREATE TABLE %s (%s VARCHAR(255) NOT NULL, %s TIMESTAMP, PRIMARY KEY(%s), INDEX %s(%s)) ENGINE = %s CHARACTER SET utf8 COLLATE utf8_general_ci" % (table_name, table_key_field, timestamp_field, table_key_field, timestamp_field, timestamp_field, DATABASE_ENGINE))

            table = tables[table_name] = Table(table_name, timestamp_field, table_key_field)

            return table


def normalize_type(field_name, field_type):
    if field_name.endswith("_ref"):
        return TYPE_REFERENCE
    elif field_type == "tinyint(1)":
        return TYPE_BOOL
    elif field_type.startswith("varchar"):
        return TYPE_STR
    elif field_type.startswith("int"):
        return TYPE_INT
    else:
        return field_type


class Table:
    def __init__(self, name, timestamp_field, key_field):
        self.name = name
        self.timestamp_field = timestamp_field
        self.key_field = key_field

        self.fields = {}
        self.fields[key_field] = TYPE_KEY
        self.fields[timestamp_field] = TYPE_TIMESTAMP

        self.list_fields = {}




def synchronize_field(cur, table, field_name, field_type, is_list, is_embedded_list):
    if is_embedded_list:
        if not table.fields.has_key(field_name):
            # table doesn't have this field yet - add it
            create_field(cur, table.name, table.key_field, field_name, TYPE_STR_LIST, False)
            table.fields[field_name] = TYPE_STR_LIST
    elif is_list:
        if not table.list_fields.has_key(field_name):
            # table doesn't have this field yet - add it
            create_field(cur, table.name, table.key_field, field_name, field_type, is_list)
            table.list_fields[field_name] = field_type
    else:
        if not table.fields.has_key(field_name):
            # table doesn't have this field yet - add it
            create_field(cur, table.name, table.key_field, field_name, field_type, is_list)
            table.fields[field_name] = field_type



def create_field(cur, table_name, table_key_field, field_name, field_type, is_list):
    if is_list:
        # this is list field - create a separate table for it
        list_table_name = "%s_%s" % (table_name, field_name)
        cur.execute("CREATE TABLE %s (id INTEGER NOT NULL AUTO_INCREMENT, %s VARCHAR(255) NOT NULL, PRIMARY KEY(id), INDEX k(%s)) ENGINE = %s CHARACTER SET utf8 COLLATE utf8_general_ci" % (list_table_name, table_key_field, table_key_field, DATABASE_ENGINE))
        create_field(cur, list_table_name, table_key_field, field_name, field_type, False)
    else:
        if field_type == TYPE_DATETIME:
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` DATETIME" % (table_name, field_name))
        elif field_type == TYPE_TIMESTAMP:
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` TIMESTAMP NOT NULL, ADD INDEX %s(%s)" % (table_name, field_name, field_name, field_name))
        elif field_type == TYPE_INT:
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` INTEGER" % (table_name, field_name))
        elif field_type == TYPE_LONG:
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` INTEGER" % (table_name, field_name))
        elif field_type == TYPE_FLOAT:
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` FLOAT" % (table_name, field_name))
        elif field_type == TYPE_BOOL:
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` BOOLEAN" % (table_name, field_name))
        elif field_type == TYPE_TEXT or field_type == TYPE_STR_LIST:
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` TEXT" % (table_name, field_name))
        elif field_type == TYPE_KEY or field_type == TYPE_REFERENCE:
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` VARCHAR(500)" % (table_name, field_name))
        elif field_type == TYPE_BLOB:
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` BLOB" % (table_name, field_name))
        else: # str
            cur.execute("ALTER TABLE %s ADD COLUMN `%s` VARCHAR(500)" % (table_name, field_name))



def mysql_to_rocket(field_type, mysql_value):
    if mysql_value == None:
        rocket_value = ""
    elif (field_type == TYPE_DATETIME or field_type == TYPE_TIMESTAMP):
        rocket_value = utils.to_iso(mysql_value)
    elif field_type == TYPE_KEY:
        rocket_value = mysql_to_rocket(TYPE_STR, mysql_value)
        if rocket_value[0] in '0123456789':
            # MYSQL ID
            rocket_value = '_%s' % rocket_value
        elif mysql_value[0] == '_':
            # APPENGINE ID
            rocket_value = rocket_value[1:]

    elif field_type == TYPE_REFERENCE:
        slash = mysql_value.find("/")
        if slash > 0:
            kind = mysql_value[:slash]
            key_name_or_id = mysql_to_rocket(TYPE_KEY, mysql_value[slash + 1:])
            rocket_value = "%s/%s" % (kind, key_name_or_id)
        else:
            logging.error("invalid reference value: %s" % mysql_value)
            rocket_value = ""
    elif field_type == TYPE_BLOB:
        rocket_value = base64.b64encode(mysql_value)
    else:
        rocket_value = (u'%s' % mysql_value).replace('|', '&#124;').encode('utf-8')

    return rocket_value



def rocket_to_mysql(field_type, rocket_value):
    if not rocket_value:
        mysql_value = None
    elif field_type == TYPE_DATETIME or field_type == TYPE_TIMESTAMP:
        mysql_value = utils.from_iso(rocket_value)
    elif field_type == TYPE_BOOL:
        mysql_value = bool(int(rocket_value))
    elif field_type == TYPE_INT:
        mysql_value = int(rocket_value)
    elif field_type == TYPE_LONG:
        mysql_value = long(rocket_value)
    elif field_type == TYPE_FLOAT:
        mysql_value = float(rocket_value)
    elif field_type == TYPE_KEY:
        if rocket_value[0] in '0123456789':
            # APPENGINE ID
            mysql_value = u'_%s' % rocket_value
        elif rocket_value[0] == '_':
            # MYSQL ID
            mysql_value = mysql_value[1:]
        else:
            mysql_value = rocket_value

    elif field_type == TYPE_REFERENCE:
        slash = rocket_value.find("/")
        if slash > 0:
            kind = rocket_value[:slash]
            key_name_or_id = rocket_to_mysql(TYPE_KEY, rocket_value[slash + 1:])
            mysql_value = "%s/%s" % (kind, key_name_or_id)
        else:
            logging.error("invalid reference value: %s" % rocket_value)
            mysql_value = None
    elif field_type == TYPE_BLOB:
        mysql_value = base64.b64decode(rocket_value)
    else:
        mysql_value = rocket_value

    return mysql_value


def replicate_in_loop():
    connect()
    read_send_receive_states()

    while True:
        while replicate_all():
            # call replicate_all until no more updates are found
            pass

        logging.info('no more updates found, idling for %d seconds' % (IDLE_TIME))

        # idle for given IDLE_TIME
        time.sleep(IDLE_TIME)


def main():
    sys.stdout = sys.stderr = o = open(LOGFILE, 'a+')
    logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s', stream=o)

    os.setegid(GID)
    os.seteuid(UID)

    replicate_in_loop()


if __name__ == "__main__":
    if daemon:
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            logging.error("fork #1 failed: %d (%s)" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")   #don't prevent unmounting....
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                logging.info("Daemon PID %d" % pid)
                open(PIDFILE,'w').write("%d"%pid)
                sys.exit(0)
        except OSError, e:
            logging.error("fork #2 failed: %d (%s)" % (e.errno, e.strerror))
            sys.exit(1)

        # start the daemon main loop
        main()
    else:
        logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s', stream=stdout)

        if in_loop:
            replicate_in_loop()
        else:
            connect()
            read_send_receive_states()
            replicate_all()
            con.close()

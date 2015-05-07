# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.conf import settings
from scrapy.exceptions import DropItem
from scrapy import log
from vietnamworks_crawler.items import JobItem
import dblite
import datetime

# remove duplicates
class DuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def close_spider(self, spider):
        log.msg('ids_seen' + str(self.ids_seen), logLevel=log.WARNING)

    def process_item(self, item, spider):
        if item['_id'] in self.ids_seen:
            raise DropItem("Duplicate item ID found: %s" % item)
        else:
            self.ids_seen.add(item['_id'])
            return item

# limit number of item returned
class MaxCountPipeline(object):
    def __init__(self):
        self.count = 1
	
    def process_item(self, item, spider):
        if spider.max_count > 0 and self.count > spider.max_count:
            raise DropItem("Maximum count (%d) exceeded: %s" % (spider.max_count, item))
        else:
            self.count = self.count + 1
            return item

# skip items older than days_limit days
class NoLaterThanDaysPipeline(object):

    def process_item(self, item, spider):
        # datetime calculation from http://pymotw.com/2/datetime/
        format = '%d/%m/%Y'
        try:
            d1 = datetime.datetime.strptime(item['date'], format)            
        # date conversion error, is 'Today'?	
        except Exception as e:
            d1 = datetime.datetime.today()
            #print type(e)     # the exception instance
            #print e.args      # arguments stored in .args
            #print e           # __str__ allows args to be printed directly
        d2 = datetime.datetime.today()
        daysDiff = (d2 - d1).days 
        if daysDiff > spider.days_limit:
            raise DropItem("Skipped job older than (%d)!" % daysDiff)
        else:
            return item

class SqlitePipeline(object):
    def __init__(self):
        self.ds = None

    def open_spider(self, spider):
        self.ds = dblite.open(JobItem, 'sqlite://jobs.sqlite:items', autocommit=True)

    def close_spider(self, spider):
        self.ds.commit()
        self.ds.close()

    def process_item(self, item, spider):
        if isinstance(item, JobItem):
            try:
                self.ds.put(item)
            except dblite.DuplicateItem:
                raise DropItem("Duplicate database item found: %s" % item)
            except Exception as err:
                print traceback.format_exc()
        else:
            raise DropItem("Unknown item type, %s" % type(item))
        return item

class RequiredFieldsPipeline(object):
    """A pipeline to ensure the item have the required fields."""

    required_fields = ('_id', 'name', 'company', 'url', 'industry', 'location', 'level', 'description')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.stats)

    def __init__(self, stats):
        self.stats = stats

    def open_spider(self, spider):
        self.stats.set_value('missing_required_field_count', 0)

    def close_spider(self, spider):
        #log.msg("missing_required_field_count: " + stats.get_value('missing_required_field_count'), logLevel=log.WARNING)
        pass

    def process_item(self, item, spider):
        for field in self.required_fields:
            if not item.get(field):
                self.stats.inc_value('missing_required_field_count')
                raise DropItem("Field '%s' missing: %r" % (field, item))
        return item


class MySQLStorePipeline(object):
    """A pipeline to store the item in a MySQL database.
    This implementation uses Twisted's asynchronous database API.
    """

    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbargs = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8',
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool('MySQLdb', **dbargs)
        return cls(dbpool)

    def process_item(self, item, spider):
        # run db query in the thread pool
        d = self.dbpool.runInteraction(self._do_upsert, item, spider)
        d.addErrback(self._handle_error, item, spider)
        # at the end return the item in case of success or failure
        d.addBoth(lambda _: item)
        # return the deferred instead the item. This makes the engine to
        # process next item (according to CONCURRENT_ITEMS setting) after this
        # operation (deferred) has finished.
        return d

    def _do_upsert(self, conn, item, spider):
        """Perform an insert or update."""
        guid = self._get_guid(item)
        now = datetime.utcnow().replace(microsecond=0).isoformat(' ')

        conn.execute("""SELECT EXISTS(
            SELECT 1 FROM website WHERE guid = %s
        )""", (guid, ))
        ret = conn.fetchone()[0]

        if ret:
            conn.execute("""
                UPDATE website
                SET name=%s, description=%s, url=%s, updated=%s
                WHERE guid=%s
            """, (item['name'], item['description'], item['url'], now, guid))
            spider.log("Item updated in db: %s %r" % (guid, item))
        else:
            conn.execute("""
                INSERT INTO website (guid, name, description, url, updated)
                VALUES (%s, %s, %s, %s, %s)
            """, (guid, item['name'], item['description'], item['url'], now))
            spider.log("Item stored in db: %s %r" % (guid, item))

    def _handle_error(self, failure, item, spider):
        """Handle occurred on db interaction."""
        # do nothing, just log
        log.err(failure)

    def _get_guid(self, item):
        """Generates an unique identifier for a given item."""
        # hash based solely in the url field
        return md5(item['url']).hexdigest()

MONGODB_SAFE = False
MONGODB_ITEM_ID_FIELD = "_id"

class MongoDBPipeline(object):
    def __init__(self, mongodb_server, mongodb_port, mongodb_db, mongodb_collection, mongodb_uniq_key,
                 mongodb_item_id_field, mongodb_safe):
        connection = pymongo.Connection(mongodb_server, mongodb_port)
        self.mongodb_db = mongodb_db
        self.db = connection[mongodb_db]
        self.mongodb_collection = mongodb_collection
        self.collection = self.db[mongodb_collection]
        self.uniq_key = mongodb_uniq_key
        self.itemid = mongodb_item_id_field
        self.safe = mongodb_safe

        if isinstance(self.uniq_key, basestring) and self.uniq_key == "":
            self.uniq_key = None

        if self.uniq_key:
            self.collection.ensure_index(self.uniq_key, unique=True)


    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(settings.get('MONGODB_SERVER', 'localhost'), settings.get('MONGODB_PORT', 27017),
                   settings.get('MONGODB_DB', 'scrapy'), settings.get('MONGODB_COLLECTION', None),
                   settings.get('MONGODB_UNIQ_KEY', None), settings.get('MONGODB_ITEM_ID_FIELD', MONGODB_ITEM_ID_FIELD),
                   settings.get('MONGODB_SAFE', MONGODB_SAFE))


    def process_item(self, item, spider):
        if self.uniq_key is None:
            result = self.collection.insert(dict(item), safe=self.safe)
        else:
            result = self.collection.update({ self.uniq_key: item[self.uniq_key] }, { '$set': dict(item) },
                                            upsert=True, safe=self.safe)

        # If item has _id field and is None
        if self.itemid in item.fields and not item.get(self.itemid, None):
            item[self.itemid] = result

        log.msg("Item %s wrote to MongoDB database %s/%s" % (result, self.mongodb_db, self.mongodb_collection),
                level=log.DEBUG, spider=spider)
        return item
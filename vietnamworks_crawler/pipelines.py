# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.conf import settings
from scrapy.exceptions import DropItem
from scrapy import log
from vietnamworks_crawler.items import JobItem
from twisted.enterprise import adbapi
from pymongo import errors
import dblite, datetime, pymongo

# remove duplicates
class DuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    #def close_spider(self, spider):
    #    log.msg('ids_seen' + str(self.ids_seen), logLevel=log.WARNING)

    def process_item(self, item, spider):
        if item['id'] in self.ids_seen:
            raise DropItem("Duplicate item ID found: %s" % item)
        else:
            self.ids_seen.add(item['id'])
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
        self.ds = dblite.open(JobItem, 'sqlite://' + spider.sqlite_file + ':items', autocommit=True)

    def close_spider(self, spider):
        self.ds.commit()
        self.ds.close()

    def process_item(self, item, spider):
        if isinstance(item, JobItem):
            try:
                self.ds.put(item)
            except dblite.DuplicateItem:
                raise DropItem("Duplicate SQLite item found: %s" % item)
        else:
            raise DropItem("Unknown item type, %s" % type(item))
        return item

class MongoDBPipeline (object):
    def __init__(self):
        self.connection = None

    def open_spider(self, spider):
        self.connection = pymongo.MongoClient()
        #self.connection = pymongo.MongoClient(settings['MONGODB_URI'])
        self.db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_COLLECTION']]

    def close_spider(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        if isinstance(item, JobItem):
            try:
                self.collection.insert_one(dict(item), upsert=True)
            except errors.DuplicateKeyError:
                raise DropItem("Duplicate MongoDB item found: %s" % item)
        else:
            raise DropItem("Unknown item type, %s" % type(item))
        return item


class RequiredFieldsPipeline(object):
    """A pipeline to ensure the item have the required fields."""
    required_fields = ('id', 'name', 'company', 'url', 'industry', 'location', 'level', 'description')

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

class MySQLPipeline(object):
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
        now = datetime.utcnow().replace(microsecond=0).isoformat(' ')

        fieldnames = ','.join([f for f in item])
        fieldnames_template = ','.join(['?' for f in item])
        SQL = 'INSERT INTO %s (%s) VALUES (%s);' % (self._table, fieldnames, fieldnames_template)
        log.msg(SQL, logLevel=log.INFO)

        try:
            self._cursor.execute(SQL)
        except sqlite3.IntegrityError:
            raise DuplicateItem('Duplicate item, %s' % item)
        except Exception, err:
            print err.args
            spider.log(e)

        self._do_autocommit()

    def _handle_error(self, failure, item, spider):
        """Handle occurred on db interaction."""
        # do nothing, just log
        log.err(failure)

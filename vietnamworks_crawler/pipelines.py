# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem
import datetime

# remove duplicates
class DuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['id'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['id'])
            return item

# limit number of item returned
class MaxCountPipeline(object):
    def __init__(self):
        self.count = 1
	
    def process_item(self, item, spider):
        if spider.max_count > 0 and self.count > spider.max_count:
            raise DropItem("Maximum count exceeded: %s" % item)
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
            raise DropItem("Skipped (%d days old): %s" % (daysDiff, item))
        else:
            return item
			

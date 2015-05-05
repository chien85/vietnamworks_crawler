# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class JobItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    _id = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    company = scrapy.Field()
    companyprofile = scrapy.Field()
    industry = scrapy.Field()
    location  = scrapy.Field()
    level = scrapy.Field()
    # salary = scrapy.Field()
    url = scrapy.Field()
    description = scrapy.Field()
    requirements = scrapy.Field()
    date = scrapy.Field()
    firstseen = scrapy.Field()
    pass

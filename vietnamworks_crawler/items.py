# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class JobItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    _id = Field() # reserved for dblite
    id = Field()
    name = Field()
    url = Field()
    company = Field()
    companyprofile = Field()
    industry = Field()
    location  = Field()
    level = Field()
    # salary = Field()
    description = Field()
    requirements = Field()
    date = Field()
    firstseen = Field()

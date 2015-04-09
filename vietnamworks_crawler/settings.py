# -*- coding: utf-8 -*-

# Scrapy settings for vnw project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'vietnamworks_crawler'

SPIDER_MODULES = ['vietnamworks_crawler.spiders']
NEWSPIDER_MODULE = 'vietnamworks_crawler.spiders'

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'

ITEM_PIPELINES = {
    'vietnamworks_crawler.pipelines.NoLaterThanDaysPipeline':100, 
    'vietnamworks_crawler.pipelines.DuplicatesPipeline': 300,
    'vietnamworks_crawler.pipelines.MaxCountPipeline': 800,
}

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
    'vietnamworks_crawler.pipelines.RequiredFieldsPipeline': 50,
    'vietnamworks_crawler.pipelines.DuplicatesPipeline': 100,
    'vietnamworks_crawler.pipelines.MaxCountPipeline': 200,
#    'vietnamworks_crawler.pipelines.SqlitePipeline': 800,
#    'vietnamworks_crawler.pipelines.MySQLPipeline': 850
    'vietnamworks_crawler.pipelines.MongoDBPipeline':900,
}
DOWNLOADER_MIDDLEWARES = {
#    'vietnamworks_crawler.middlewares.IgnoreVisitedItems': 500,
    'vietnamworks_crawler.middlewares.GoogleCacheMiddleware': 600,
}

# MySQL settings
MYSQL_HOST = 'localhost'
MYSQL_DBNAME = 'mysql'
MYSQL_USER = 'admin'
MYSQL_PASSWD = 'password'

# MongoDB settings
MONGODB_SERVER = 'localhost' # to provide username and password, enter mongodb://user:pass@host:port
MONGODB_PORT = 27017
MONGODB_DB = 'mongodb'
MONGODB_COLLECTION = 'items'
MONGODB_UNIQ_KEY = 'url'
MONGODB_ITEM_ID_FIELD = 'id'
MONGODB_SAFE = False

# Mail SMTP settings
# for Gmail: https://support.google.com/a/answer/176600?hl=en
MAIL_ENABLED = True # enable/disable mailer
MAIL_HOST = 'smtp.gmail.com'
MAIL_FROM = 'username@gmail.com'
MAIL_TO = 'your.email@address.com' # address to notify
MAIL_USER  = 'username@gmail.com' # if omitted, the MAIL_USER setting will be used. If not given, no SMTP authentication will be performed.
MAIL_PASS = 'password'
MAIL_PORT = 465
MAIL_TLS = False # enforce using SMTP STARTTLS
MAIL_SSL = True # enforce using a secure SSL connection

# Google Cache settings
GOOGLE_CACHE_DOMAINS = ['vietnamworks.com', 'www.vietnamworks.com']
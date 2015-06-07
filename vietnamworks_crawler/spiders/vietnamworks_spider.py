from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.mail import MailSender
from scrapy.xlib.pydispatch import dispatcher
from scrapy.http import HtmlResponse
from scrapy.signalmanager import SignalManager
from scrapy import signals
from vietnamworks_crawler.items import JobItem
import re, datetime


class VietnamWorksSpider(CrawlSpider):
    name = 'vietnamworks'
    allowed_domains = ['vietnamworks.com']
    # scrape first 99 pages
    start_urls = ['http://www.vietnamworks.com/job-search/all-jobs/page-%d' % d for d in range(1, 100) ]
    rules = [Rule(LinkExtractor(allow=['/.*-\d+-jd']), 'parse_job', follow=False)]

    # pass additional arguments to the spider
    def __init__(self, mail_enabled=0, max_count=0, sqlite_file='jobs.sqlite', *args, **kwargs):
        self.mail_enabled = int(mail_enabled)
        self.max_count = int(max_count)
        self.sqlite_file = sqlite_file
        super(VietnamWorksSpider, self).__init__(*args, **kwargs)
        # register a signal listener to listen for spider_closed signal
        SignalManager(dispatcher.Any).connect(
            self.spider_closed_handler, signal=signals.spider_closed)

    def parse_job(self, response):
        job = JobItem()
        job['url'] = response.url
        job['id'] = re.sub(r'.*-(\d+)-jd', r'\1',response.url)
        job['name'] = response.xpath('//*[@itemprop="title"]/text()').extract()[0]
        job['industry'] = ','.join(response.xpath('//h5/text()[contains(.,"Job categories")]/../..//a/text()').extract())
        job['location'] = ','.join(response.xpath('//*[@itemprop="address"]//a/text()').extract())
        job['description'] = ''.join(response.xpath('//*[@itemprop="description"]/node()').extract())
        job['requirements'] = ''.join(response.xpath('//*[@itemprop="experienceRequirements "]/node()').extract())
        job['level'] = response.xpath('//h5/text()[contains(.,"Job level")]/../..//a/text()').extract()[0]
        job['company'] = response.xpath('//*[@itemprop="name"]//a/text()').extract()[0]
        job['companyprofile'] = ''.join(response.xpath('//*[@id="companyprofile"]/node()').extract())
        job['preferredlanguage'] = response.xpath('//h5/text()[contains(.,"Preferred language")]/../../p/text()').extract()[0]
        now = datetime.datetime.utcnow() # use UTC time (timezone independent)
        job['firstseen'] = now
        job['date'] = now.date() # aggregated from first-seen
        # salary information requires login
        # job['salary'] = sel.xpath('//span[contains(@class,"hidden-xs")/span/strong/text()').extract()

        yield job
			
    def spider_closed_handler(self, spider):
        # notify admin on some critical error events such as missing of required fields (incorrect pattern)
        # http://stackoverflow.com/questions/12394184/scrapy-call-a-function-when-a-spider-quits
        settings = self.settings
        # send email in case a missing required field item has been found
        # possibly, one or more regex pattern is no longer valid
        # allow enable mail by settings or commandline argument: scrapy crawl vietnamworks -a max_count=10 -a mail_enabled=1
        if (settings['MAIL_ENABLED'] or self.mail_enabled) \
                and self.crawler.stats.get_value('missing_required_field_count'):
            mailer = MailSender.from_settings(settings)
            body = "Global stats\n\n"
            body += "\n".join("%-50s : %s" % i for i in self.crawler.stats.get_stats().items())
            mailer.send(to=[settings['MAIL_TO']], subject="vietnamworks_crawler: Error Report", body=body)

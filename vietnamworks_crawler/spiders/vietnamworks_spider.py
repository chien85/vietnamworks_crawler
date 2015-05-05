from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from vietnamworks_crawler.items import JobItem
import re, datetime


class VietnamWorksSpider(CrawlSpider):
    name = 'vietnamworks'
    allowed_domains = ['vietnamworks.com']
    # scrape first 99 pages
    start_urls = ['http://www.vietnamworks.com/job-search/all-jobs/page-%d' % d for d in range(1, 100) ]
    # rules = [Rule(LinkExtractor(allow=['/.*?-\d+-jv']), 'parse_list')]
    rules = [Rule(LinkExtractor(allow=['/.*-\d+-jd']), 'parse_job', follow=False)]

    # pass additional arguments to the spider
    def __init__(self, days_limit=0, max_count=0, *args, **kwargs):
        #self.days_limit = int(days_limit)
        self.max_count = int(max_count)
        super(VietnamWorksSpider, self).__init__(*args, **kwargs)

    def parse_job(self, response):
            job = JobItem()
            job['url'] = response.url
            job['id'] = re.sub(r'.*-(\d+)-jd', r'\1',response.url)
            job['name'] = response.xpath('//*[@itemprop="title"]/text()').extract()[0]
            job['industry'] = ','.join(response.xpath('//*[@itemprop="industry"]/*/text()').extract())
            job['location'] = ','.join(response.xpath('//*[@itemprop="address"]//text()').extract())
            job['description'] = ''.join(response.xpath('//*[@itemprop="description"]/node()').extract())
            job['requirements'] = ''.join(response.xpath('//*[@itemprop="experienceRequirements"]/node()').extract())
            job['level'] = response.xpath('//*[@itemprop="occupationalCategory"]/*/text()').extract()[0]
            job['company'] = response.xpath('//*[@itemprop="name"]//text()').extract()[0]
            job['companyprofile'] = ''.join(response.xpath('//*[@id="companyprofile"]/node()').extract())
            now = datetime.datetime.utcnow() # use UTC time (timezone independent)
            job['firstseen'] = now
            job['date'] = now.date() # aggregated from first-seen
            # salary information requires login
            # job['salary'] = sel.xpath('//span[contains(@class,"hidden-xs")/span/strong/text()').extract()

            yield job
			

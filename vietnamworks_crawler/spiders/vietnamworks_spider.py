from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from vietnamworks_crawler.items import JobItem

class VietnamWorksSpider(CrawlSpider):
	name = 'vietnamworks'
	allowed_domains = ['vietnamworks.com']
	start_urls = ['http://www.vietnamworks.com/job-search/all-jobs/page-1']
	# rules = [Rule(LinkExtractor(allow=['/.*?-\d+-jv']), 'parse_list')]
	rules = [Rule(LinkExtractor(allow=['/job-search/all-jobs(/page-\d+)?']), 'parse_list', follow=True)]
	
	# pass additional arguments to the spider
	def __init__(self, days_limit=0, max_count=0, *args, **kwargs):
		self.days_limit = int(days_limit)
		self.max_count = int(max_count)
		super(VietnamWorksSpider, self).__init__(*args, **kwargs)
		
	def parse_list(self, response):
		for sel in response.xpath('//tr[contains(@class,"job-post")]/td/div'):
			job = JobItem()
			job['url'] = sel.xpath('.//a[contains(@class,"job-title")]/@href').extract()
			job['id'] = sel.xpath('.//a[contains(@class,"job-title")]/@href').re(r'.*-(\d+)-jd')[0].strip() # .re returns list instead of string
			job['name'] = sel.xpath('.//a[contains(@class,"job-title")]/text()').extract()
			job['location'] = sel.xpath('.//p[contains(@class,"job-info")]/span/span[1]/text()').extract()
			job['level'] = sel.xpath('.//p[contains(@class,"job-info")]/span/span[2]/text()').extract()
			job['company'] = sel.xpath('.//div[contains(@class,"company-name")]/@title').extract()
			job['date'] = sel.xpath('.//div[contains(@class,"extra-info")]/div/div/span[1]/span/span/text()').re(r'Posted:\s+(.*)')[0].strip() #regex
			# salary information requires login
			#job['salary'] = sel.xpath('//span[contains(@class,"hidden-xs")/span/strong/text()').extract()
			
			yield job
			

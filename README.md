# vietnamworks_crawler
A Scrapy's Crawler for VietnamWorks.com.

It uses [scrapy] engine(http://scrapy.org/).

## How to run:
1. With scrapy installed, go the project home folder and execute: 
```
git clone https://github.com/trananhtuan/vietnamworks_crawler
cd vietnamworks_crawler
scrapy crawl vietnamworks
```
In order to avoid crawled pages between runs (ie. cron), append "-s JOBDIR=cache" to the last command
```
/usr/local/bin/scrapy crawl vietnamworks -s JOBDIR=cache
```
2. Check jobs.sqlite for result
3. Feel free to modify and make your commits



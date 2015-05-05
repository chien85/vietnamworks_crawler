# vietnamworks_crawler
A VietnamWorks Crawler and RSS.

It uses [scrapy] (http://scrapy.org/) engine.

## Deploy on OpenShift
To deploy this script on OpenShift, you will need to use a python cartridge with an added cron cartridge, then you need to clone the source code to ~/app-root/runtime/repo

OpenShift can do most of these steps automatically for you. Step by step guide is as follow:

1. Go to [OpenShift application console] (https://openshift.redhat.com/app/console/applications), select Add Application to create a new gear
2. Select Python (2.7 recommended) on the cartridge selection page
3. Enter a public domain for your app or use default, select an appropriate gear
4. On source code field, enter 
```
https://github.com/trananhtuan/vietnamworks_crawler
```
leave branch empty (or enter the branch you want to use). Click Create Application and wait for OpenShift to create your gear
5. Go back to [OpenShift application console] (https://openshift.redhat.com/app/console/applications), select your newly created gear
6. On the application management page, select "see the list of cartridges you can add" and select Cron to add cron cartridge to your gear
7. Go to your application domain to check

To deploy to an existing python gear (python 2.7 recommended), please follow the following steps:
1. Go to OpenShift application console and add cron to your gear 
2. Bare-clone and mirror-push the source code to your gear
```
git clone --bare https://github.com/trananhtuan/vietnamworks_crawler
cd old-repository.git
git push --mirror ssh://APP_USERNAME@APPNAME-DOMAIN.rhcloud.com/~/git/tmp.git/
cd ..
rm -rf vietnamworks_crawler.git
```
2. Go to your application domain to check

RSS will be ready as the cron runs for the first time. By default, a cron job runs hourly to crawl new pages.

## Run manually:
With scrapy installed, go the project home folder and execute: 
```
git clone https://github.com/trananhtuan/vietnamworks_crawler
cd vietnamworks_crawler
scrapy crawl vietnamworks
```
In order to avoid crawled pages between runs (ie. cron), append "-s JOBDIR=cache" to the last command
```
scrapy crawl vietnamworks -s JOBDIR=cache
```
By default, scraped items are saved in jobs.sqlite


Feel free to modify and make your commits


#!/bin/bash
cd $OPENSHIFT_REPO_DIR
# set log level to INFO, save session info to folder 'cache'
# modify settings.py with your mail SMTP settings and add "-a mail_enabled=1" to receive emails on pattern error
$OPENSHIFT_HOMEDIR/python/virtenv/bin/scrapy crawl -L INFO -s JOBDIR=cache vietnamworks
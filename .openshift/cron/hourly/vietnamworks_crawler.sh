#!/bin/bash
cd $OPENSHIFT_REPO_DIR
$OPENSHIFT_HOMEDIR/python/virtenv/bin/scrapy crawl vietnamworks -s JOBDIR=cache
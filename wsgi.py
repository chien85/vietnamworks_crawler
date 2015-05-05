#!/usr/bin/python
import csv, re, traceback, datetime, urlparse, logging, sqlite3, os
import PyRSS2Gen

def smart_truncate(content, length=100, suffix='...'):
    if len(content) <= length:
        return content
    else:
        return content[:length].rsplit(' ', 1)[0] + suffix

locations = {'29':'Ho Chi Minh',
    '24':'Ha Noi',
    '71':'Mekong Delta',
    '2':'An Giang',
    '3':'Ba Ria - Vung Tau',
    '4':'Bac Can',
    '5':'Bac Giang',
    '6':'Bac Lieu',
    '7':'Bac Ninh',
    '8':'Ben Tre',
    '9':'Bien Hoa',
    '10':'Binh Dinh',
    '11':'Binh Duong',
    '12':'Binh Phuoc',
    '13':'Binh Thuan',
    '14':'Ca Mau',
    '15':'Can Tho',
    '16':'Cao Bang',
    '17':'Da Nang',
    '18':'Dac Lac',
    '69':'Dien Bien',
    '19':'Dong Nai',
    '20':'Dong Thap',
    '21':'Gia Lai',
    '22':'Ha Giang',
    '23':'Ha Nam',
    '25':'Ha Tay',
    '26':'Ha Tinh',
    '27':'Hai Duong',
    '28':'Hai Phong',
    '30':'Hoa Binh',
    '31':'Hue',
    '32':'Hung Yen',
    '33':'Khanh Hoa',
    '34':'Kon Tum',
    '35':'Lai Chau',
    '36':'Lam Dong',
    '37':'Lang Son',
    '38':'Lao Cai',
    '40':'Nam Dinh',
    '41':'Nghe An',
    '42':'Ninh Binh',
    '43':'Ninh Thuan',
    '44':'Phu Tho',
    '45':'Phu Yen',
    '46':'Quang Binh',
    '47':'Quang Nam',
    '48':'Quang Ngai',
    '49':'Quang Ninh',
    '50':'Quang Tri',
    '51':'Soc Trang',
    '52':'Son La',
    '53':'Tay Ninh',
    '54':'Thai Binh',
    '55':'Thai Nguyen',
    '56':'Thanh Hoa',
    '57':'Thua Thien-Hue',
    '58':'Tien Giang',
    '59':'Tra Vinh',
    '60':'Tuyen Quang',
    '61':'Kien Giang',
    '62':'Vinh Long',
    '63':'Vinh Phuc',
    '65':'Yen Bai',
    '66':'Other',
    '70':'International',
    '72':'Hau Giang',
    '39':'Long An'}
industries = {'1':'Accounting',
    '2':'Administrative/Clerical',
    '3':'Advertising/Promotion/PR',
    '4':'Agriculture/Forestry',
    '37':'Airlines/Tourism/Hotel',
    '5':'Architecture/Interior Design',
    '10':'Arts/Design',
    '58':'Auditing',
    '67':'Automotive',
    '42':'Banking',
    '43':'Chemical/Biochemical',
    '7':'Civil/Construction',
    '8':'Consulting',
    '11':'Customer Service',
    '12':'Education/Training',
    '64':'Electrical/Electronics',
    '15':'Entry level',
    '16':'Environment/Waste Services',
    '17':'Executive management',
    '18':'Expatriate Jobs in Vietnam',
    '19':'Export-Import',
    '63':'Fashion/Lifestyle',
    '59':'Finance/Investment',
    '54':'Food &amp; Beverage',
    '36':'Freight/Logistics',
    '22':'Health/Medical Care',
    '66':'High Technology',
    '23':'Human Resources',
    '68':'Industrial Products',
    '24':'Insurance',
    '57':'Internet/Online Media',
    '47':'Interpreter/Translator',
    '55':'IT - Hardware/Networking',
    '35':'IT - Software',
    '25':'Legal/Contracts',
    '62':'Luxury Goods',
    '27':'Marketing',
    '65':'Mechanical',
    '21':'NGO/Non-Profit',
    '28':'Oil/Gas',
    '71':'Overseas Jobs',
    '6':'Pharmaceutical/Biotech',
    '69':'Planning/Projects',
    '26':'Production/Process',
    '49':'Purchasing/Supply Chain',
    '70':'QA/QC',
    '30':'Real Estate',
    '32':'Retail/Wholesale',
    '33':'Sales',
    '34':'Sales Technical',
    '56':'Securities &amp; Trading',
    '41':'Telecommunications',
    '51':'Temporary/Contract',
    '52':'Textiles/Garments/Footwear',
    '48':'TV/Media/Newspaper',
    '53':'Warehouse',
    '39':'Other',}

levels = ['New Grad/Entry Level/Internship',
    'Experienced (Non-Manager)',
    'Team Leader/Supervisor',
    'Manager',
    'Vice Director',
    'Director',
    'CEO',
    'Vice President',
    'President',]

DB_FILE='jobs.sqlite'

# uncomment these next lines to active python virtual environment on OpenShift
#virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
#virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
#try:
#    execfile(virtualenv, dict(__file__=virtualenv))
#except IOError:
#    pass

#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
#

def application(environ, start_response):

    ctype = 'text/plain'
    path_prefix = '/cgi'
    if environ['PATH_INFO'] == path_prefix + '/health':
        response_body = "1"
    elif environ['PATH_INFO'] == path_prefix + '/env':
        response_body = ['%s: %s' % (key, value)
                    for key, value in sorted(environ.items())]
        response_body = '\n'.join(response_body)
    elif environ['PATH_INFO'] == path_prefix + '/rss':
        ctype = 'application/rss+xml'

        # Returns a dictionary containing lists as values.
        qs = urlparse.parse_qs(environ['QUERY_STRING'])

        # In this idiom you must issue a list containing a default value.
        name = qs.get('name', [''])[0] # get only first param
        value = qs.get('value', [''])[0]
        max = int(qs.get('max', ['0'])[0])
        loc = qs.get('location', ['']) # get a list of loc ie. location=1&location=2..
        ind = qs.get('industry', ['']) # get a list of industries ie. industry=1&industry=2
        min_level = int(qs.get('level', ['0'])[0])

        # min_level == 2 means Supervisor, == 3 means Manager etc
        selected_levels = levels[min_level:]

        loc = map(str.strip, loc)
        selected_locations = [locations[l] for l in loc if l]

        ind = map(str.strip, ind)
        selected_industries = [industries[i] for i in ind if i]

        # construct select query
        q = "SELECT * FROM items "
        filters = [' OR '.join(["(location LIKE '%%%s%%')" %s for s in selected_locations if selected_locations])]
        filters.append(' OR '.join(["(level = '%s')" %s for s in selected_levels if min_level > 0]))
        filters.append(' OR '.join(["(industry LIKE '%%%s%%')" %s for s in selected_industries if selected_industries]))
        # workaround to remove empty string from list
        filters = filter(None, filters)
        if filters:
            q += ' WHERE ' + 'AND '.join('(%s)' %s for s in filters if s)
        q += " ORDER BY firstseen DESC LIMIT %d " % (max if (max > 0 and max < 50) else 50)
        print q
        items = []

        con = sqlite3.connect(DB_FILE)
        with con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(q)

            matches = cur.fetchall()
            # create feed items
            for row in matches:
                item = PyRSS2Gen.RSSItem(
                    title = row['name'],
                    link = row['url'],
                    description = 'Company :<span id="location">' + row['company'] + '</span><br />' \
                        + 'Location: <span id="location">' + row['location'] + '</span><br />' \
                        + 'Industry: <span id="industry">' + row['industry'] + '</span><br />' \
                        + 'Level: <span id="level">' + row['level'] + '</span><br />' \
                        + '<span id="companyprofile">' + smart_truncate(row['companyprofile'], 150) + '</span><br />' \
                        + '<h3>Description</h3><p><span id="description">' + smart_truncate(row['description'], 250) + '</span></p>' \
                        + '<h3>Requirements</h3><p><span id="requirements">' + smart_truncate(row['requirements'], 250) + '</span></p>',
                        #+ 'Date: <span id="date">' + row['date'] + '</span><br />',
                    guid = PyRSS2Gen.Guid(row['url']),
                    #pubDate = row['date'],
                    pubDate = datetime.datetime.strptime(row['firstseen'], '%Y-%m-%d %H:%M:%S.%f').strftime("%a, %d %b %Y %H:%M:%S +0000"),
                )
                items.append(item)

        rss = PyRSS2Gen.RSS2(
            title = "VietnamWorks Job Feed",
            link = "http://www.VietnamWorks.com",
            description = "The latest jobs from VietnamWorks."
                          "Usage: /rss?location=24&location=29&level=3&industry=23&industry=7",
            lastBuildDate = datetime.datetime.now(),
            items = items)

        response_body = rss.to_xml("UTF-8")
    else:
        ctype = 'text/html'
        response_body = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
  <title>Welcome to OpenShift</title>
<style>

/*!
 * Bootstrap v3.0.0
 *
 * Copyright 2013 Twitter, Inc
 * Licensed under the Apache License v2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Designed and built with all the love in the world @twitter by @mdo and @fat.
 */

.logo a {
  display: block;
  width: 100%;
  height: 100%;
}
*, *:before, *:after {
    -moz-box-sizing: border-box;
    box-sizing: border-box;
}
aside,
footer,
header,
hgroup,
section{
  display: block;
}
body {
  color: #404040;
  font-family: "Helvetica Neue",Helvetica,"Liberation Sans",Arial,sans-serif;
  font-size: 14px;
  line-height: 1.4;
}

html {
  font-family: sans-serif;
  -ms-text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
}
ul {
    margin-top: 0;
}
.container {
  margin-right: auto;
  margin-left: auto;
  padding-left: 15px;
  padding-right: 15px;
}
.container:before,
.container:after {
  content: " ";
  /* 1 */

  display: table;
  /* 2 */

}
.container:after {
  clear: both;
}
.row {
  margin-left: -15px;
  margin-right: -15px;
}
.row:before,
.row:after {
  content: " ";
  /* 1 */

  display: table;
  /* 2 */

}
.row:after {
  clear: both;
}
.col-sm-6, .col-md-6, .col-xs-12 {
  position: relative;
  min-height: 1px;
  padding-left: 15px;
  padding-right: 15px;
}
.col-xs-12 {
  width: 100%;
}

@media (min-width: 768px) {
  .container {
    width: 750px;
  }
  .col-sm-6 {
    float: left;
  }
  .col-sm-6 {
    width: 50%;
  }
}

@media (min-width: 992px) {
  .container {
    width: 970px;
  }
  .col-md-6 {
    float: left;
  }
  .col-md-6 {
    width: 50%;
  }
}
@media (min-width: 1200px) {
  .container {
    width: 1170px;
  }
}

a {
  color: #069;
  text-decoration: none;
}
a:hover {
  color: #EA0011;
  text-decoration: underline;
}
hgroup {
  margin-top: 50px;
}
footer {
    margin: 50px 0 25px;
    font-size: 11px
}
h1, h2, h3 {
  color: #000;
  line-height: 1.38em;
  margin: 1.5em 0 .3em;
}
h1 {
  font-size: 25px;
  font-weight: 300;
  border-bottom: 1px solid #fff;
  margin-bottom: .5em;
}
h1:after {
  content: "";
  display: block;
  width: 100%;
  height: 1px;
  background-color: #ddd;
}
h2 {
  font-size: 19px;
  font-weight: 400;
}
h3 {
  font-size: 15px;
  font-weight: 400;
  margin: 0 0 .3em;
}
p {
  margin: 0 0 2em;
}
p + h2 {
  margin-top: 2em;
}
html {
  background: #f5f5f5;
  height: 100%;
}
code {
  background-color: white;
  border: 1px solid #ccc;
  padding: 1px 5px;
  color: #888;
}
pre {
  display: block;
  padding: 13.333px 20px;
  margin: 0 0 20px;
  font-size: 13px;
  line-height: 1.4;
  background-color: #fff;
  border-left: 2px solid rgba(120,120,120,0.35);
  white-space: pre;
  white-space: pre-wrap;
  word-break: normal;
  word-wrap: break-word;
  overflow: auto;
  font-family: Menlo,Monaco,"Liberation Mono",Consolas,monospace !important;
}

</style>
</head>
<body>
<section class='container'>
          <hgroup>
            <h1>Welcome to the unofficial VietnamWorks Job Feed</h1>
          </hgroup>

        <div class="row">
          <section class='col-xs-12 col-sm-6 col-md-6'>
            <section>
              <h2>What is this?</h2>
                <p>VJF is the unofficial RSS feed for VietnamWorks.com with some neat features. It is intended to be used in conjunction with RSS Readers, ie <a href="http://www.feedly.com">Feedly</a>, or automation recipes like the one from <a href="http://www.ifttt.com/">IFTTT</a>.</p>
                <h3>How to use?</h3>
				<p>Just add this feed with your selected parameters to your feed reader. rss?level=LEVEL&max=MAX&location=LOCATION_ID1&location=LOCATION_ID2&industry=INDUSTRY_ID1&industry=INDUSTRY_ID2"</p>
                <ul>
				    <li>LEVEL: Minimum job level, detailed <a href="#joblevels">here</a>.</li>
					<li>MAX: Maximum number of returned items, max = 50, default = 50.</li>
					<li>LOCATION_IDx: Filter jobs by the location, can be chained together such as location=24&location=29 (filter jobs in Hanoi and HCMC), detailed <a href="#location">here</a>.</li>
					<li>INDUSTRY_IDx: Filter jobs by industries, can be chained together location=23&location=52 (filter jobs in Human Resources and Textile/Garment/Footwear), detailed <a href="#industries">here</a>.</li>
				</ul>

                <h3>Usage Notes</h3>
			<ul>
				<li>This feed is real-time. It is refresh on intervals.</li>
				<li>Reposted jobs (jobs with the same ID) are not to be included in the feed.</li>
				<li>This feed comes at no warranty whatsoever. Use at your own risk.</li>
			</ul>

			<h3>Credits</h3>
			<p>This is made possible by:</p>
			<ul>
				<li><a href="http://www.openshift.com">OpenShift</a> - For the hardware and a wonderful development environment</>
				<li><a href="http://www.python.org">Python</a> - For writing this without learning at all</>
				<li><a href="http://www.scrapy.org">Scrapy</a> - a Python web scraping framework</>
				<li><a href="http://www.dalkescientific.com/Python/PyRSS2Gen.html">PyRSS2Gen</a> - a library for generating RSS</>
			</ul>
			<p>And a weekend of mine ;)</p>

            </section>

          </section>
          <section class="col-xs-12 col-sm-6 col-md-6">

                <h2>Reference</h2>
				<a name="joblevels"></a>
				<h3>Job Levels</h3>
				<p>Filter jobs by specifying minimum job level.</p>
				<pre>0 = New Grad/Entry Level/Internship (Default)
1 = Experienced
2 = Team Leader/Supervisor
3 = Manager
4 = Vice Director
5 = Director
6 = CEO
7 = Vice President
8 = President</pre>
				<a name="locations"></a>
                <h3>Locations</h3>
				<p>Filter jobs by one or multiple locations. Valid LOCATION_ID are as follows:</p>
				<pre>All Locations (Default),
29=&#39;Ho Chi Minh&#39;,
24=&#39;Ha Noi&#39;,
71=&#39;Mekong Delta&#39;,
2=&#39;An Giang&#39;,
3=&#39;Ba Ria - Vung Tau&#39;,
4=&#39;Bac Can&#39;,
5=&#39;Bac Giang&#39;,
6=&#39;Bac Lieu&#39;,
7=&#39;Bac Ninh&#39;,
8=&#39;Ben Tre&#39;,
9=&#39;Bien Hoa&#39;,
10=&#39;Binh Dinh&#39;,
11=&#39;Binh Duong&#39;,
12=&#39;Binh Phuoc&#39;,
13=&#39;Binh Thuan&#39;,
14=&#39;Ca Mau&#39;,
15=&#39;Can Tho&#39;,
16=&#39;Cao Bang&#39;,
17=&#39;Da Nang&#39;,
18=&#39;Dac Lac&#39;,
69=&#39;Dien Bien&#39;,
19=&#39;Dong Nai&#39;,
20=&#39;Dong Thap&#39;,
21=&#39;Gia Lai&#39;,
22=&#39;Ha Giang&#39;,
23=&#39;Ha Nam&#39;,
25=&#39;Ha Tay&#39;,
26=&#39;Ha Tinh&#39;,
27=&#39;Hai Duong&#39;,
28=&#39;Hai Phong&#39;,
30=&#39;Hoa Binh&#39;,
31=&#39;Hue&#39;,
32=&#39;Hung Yen&#39;,
33=&#39;Khanh Hoa&#39;,
34=&#39;Kon Tum&#39;,
35=&#39;Lai Chau&#39;,
36=&#39;Lam Dong&#39;,
37=&#39;Lang Son&#39;,
38=&#39;Lao Cai&#39;,
40=&#39;Nam Dinh&#39;,
41=&#39;Nghe An&#39;,
42=&#39;Ninh Binh&#39;,
43=&#39;Ninh Thuan&#39;,
44=&#39;Phu Tho&#39;,
45=&#39;Phu Yen&#39;,
46=&#39;Quang Binh&#39;,
47=&#39;Quang Nam&#39;,
48=&#39;Quang Ngai&#39;,
49=&#39;Quang Ninh&#39;,
50=&#39;Quang Tri&#39;,
51=&#39;Soc Trang&#39;,
52=&#39;Son La&#39;,
53=&#39;Tay Ninh&#39;,
54=&#39;Thai Binh&#39;,
55=&#39;Thai Nguyen&#39;,
56=&#39;Thanh Hoa&#39;,
57=&#39;Thua Thien-Hue&#39;,
58=&#39;Tien Giang&#39;,
59=&#39;Tra Vinh&#39;,
60=&#39;Tuyen Quang&#39;,
61=&#39;Kien Giang&#39;,
62=&#39;Vinh Long&#39;,
63=&#39;Vinh Phuc&#39;,
65=&#39;Yen Bai&#39;,
66=&#39;Other&#39;,
70=&#39;International&#39;,
72=&#39;Hau Giang&#39;,
39=&#39;Long An&#39;</pre>
				<a name="industries"></a>
                <h3>Industries</h3>
                <p>Filter jobs by one or multiple industries. Valid INDUSTRY_ID are as follows:</p>
				<pre>
All categories (Default)
1=Accounting
2=Administrative/Clerical
3=Advertising/Promotion/PR
4=Agriculture/Forestry
37=Airlines/Tourism/Hotel
5=Architecture/Interior Design
10=Arts/Design
58=Auditing
67=Automotive
42=Banking
43=Chemical/Biochemical
7=Civil/Construction
8=Consulting
11=Customer Service
12=Education/Training
64=Electrical/Electronics
15=Entry level
16=Environment/Waste Services
17=Executive management
18=Expatriate Jobs in Vietnam
19=Export-Import
63=Fashion/Lifestyle
59=Finance/Investment
54=Food &amp; Beverage
36=Freight/Logistics
22=Health/Medical Care
66=High Technology
23=Human Resources
68=Industrial Products
24=Insurance
57=Internet/Online Media
47=Interpreter/Translator
55=IT - Hardware/Networking
35=IT - Software
25=Legal/Contracts
62=Luxury Goods
27=Marketing
65=Mechanical
21=NGO/Non-Profit
28=Oil/Gas
71=Overseas Jobs
6=Pharmaceutical/Biotech
69=Planning/Projects
26=Production/Process
49=Purchasing/Supply Chain
70=QA/QC
30=Real Estate
32=Retail/Wholesale
33=Sales
34=Sales Technical
56=Securities &amp; Trading
41=Telecommunications
51=Temporary/Contract
52=Textiles/Garments/Footwear
48=TV/Media/Newspaper
53=Warehouse
39=Other
				</pre>
          </section>
        </div>

        <footer>
          <div class="logo"><a href="https://www.openshift.com/"></a></div>
        </footer>
</section>
</body>
</html>'''

    status = '200 OK'
    response_headers = [('Content-Type', ctype), ('Content-Length', str(len(response_body)))]
    #
    start_response(status, response_headers)
    return [response_body]

#
# Below for testing only
#
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8051, application)
    # Wait for a single request, serve it and quit.
    httpd.handle_request()
    httpd.serve_forever()
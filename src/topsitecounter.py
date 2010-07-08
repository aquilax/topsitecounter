# -*- encoding: utf-8 -*-
import os
from base64 import b64decode
from urlparse import urlparse

from data import *
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

def get_viz(visits):
  t = '<script type="text/javascript" src="http://www.google.com/jsapi"></script>'
  t = t + '<script type="text/javascript">'
  t = t + '    google.load("visualization", "1", {packages:["linechart"]});'
  t = t + '    google.setOnLoadCallback(drawChart);'
  t = t + '    function drawChart() {'
  t = t + '      var data = new google.visualization.DataTable();'
  t = t + "      data.addColumn('string', 'Date');"
  t = t + "      data.addColumn('number', 'visits');"
  t = t + "      data.addColumn('number', 'impressions');"
  cnt = len(visits)
  t = t + '     data.addRows('+str(cnt)+');';
  i = 0
  cnt = cnt-1
  for row in visits:
    t = t + "data.setValue("+str(cnt-i)+", 0, '"+str(row.date)+"');"
    t = t + "data.setValue("+str(cnt-i)+", 1, "+str(row.vis)+");"
    t = t + "data.setValue("+str(cnt-i)+", 2, "+str(row.imp)+");"
    i = i+1
  t = t + "var chart = new google.visualization.LineChart(document.getElementById('chart_div'));"
  t = t + "chart.draw(data, {width: 600, height: 400, min: 0, legend: 'bottom', title: 'Statistics'});"
  t = t + "}"
  t = t + "</script>"
  t = t + '<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"></script><script type="text/javascript" src="/js/jquery.tablesorter.min.js"></script><script type="text/javascript">$(document).ready(function(){$("#sites").tablesorter();});</script>'
  return t

class MainPage(webapp.RequestHandler):
  def get(self):
    q = MySite.all().order('-last_access')
    include = '<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"></script><script type="text/javascript" src="/js/jquery.tablesorter.min.js"></script><script type="text/javascript">$(document).ready(function(){$("#sites").tablesorter();});</script>'
    data = {
      'sites': q.fetch(50),
      'title': "Home",
      'include': include,
      'content': "templates/index.html",
    }
    path = os.path.join(os.path.dirname(__file__), 'main.html')
    self.response.out.write(template.render(path, data))

class TrackPage(webapp.RequestHandler):
  def get(self):
    o = urlparse(self.request.referer)
    ref = o.hostname;
    ip = self.request.remote_addr;
    save(ref, ip);
    self.response.headers["Content-Type"] = 'image/gif'
    trans_gif_64 = "R0lGODlhAQABAIAAAAAAAAAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
    self.response.out.write(b64decode(trans_gif_64));

class ShowPage(webapp.RequestHandler):

  def get(self, ref):
    #try:
      site = searchsite(ref)
      site = site[0]
      visits = search_visists(site, 1)
      data = {
        'site':site,
        'visits': visits,
        'title': ref,
        'include': get_viz(visits),
        'content': "templates/show.html",
      }
      path = os.path.join(os.path.dirname(__file__), 'main.html')
      self.response.out.write(template.render(path, data))
    #except:
    #  self.error(404)

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/t', TrackPage),
                                      ('/show/(.*)', ShowPage),
                                      ],
                                     debug=False)

def profile_main():
    # This is the main function for profiling
    # We've renamed our original main() above to real_main()
    import cProfile, pstats
    prof = cProfile.Profile()
    prof = prof.runctx("real_main()", globals(), locals())
    print "<pre>"
    stats = pstats.Stats(prof)
    stats.sort_stats("time")  # Or cumulative
    stats.print_stats(80)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    print "</pre>"

def real_main():
    run_wsgi_app(application)

main = real_main

if __name__ == "__main__":
    main()
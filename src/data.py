from datetime import datetime

from google.appengine.ext import db
from google.appengine.api import memcache


__author__="aquilax"
__date__ ="$Feb 20, 2010 8:15:35 AM$"


class MySite(db.Model):
  url = db.StringProperty(verbose_name="Url")
  created = db.DateTimeProperty(verbose_name="Addred", auto_now_add=True)
  views = db.IntegerProperty(default=1)
  last_access = db.DateTimeProperty(verbose_name="Last accessed", auto_now_add=True)

class MyVisit(db.Model):
  site = db.ReferenceProperty(MySite)
  vis =  db.IntegerProperty(default=1)
  imp =  db.IntegerProperty(default=1)
  date = db.DateProperty(auto_now_add=True)

def save(ref, ip):
  if (ref is None):
    return
  site = searchsite(ref)
  hash = ref+"|"+ip;
  if (not site):
    memcache.add(key=hash, value=1 , time=86400);
    site = MySite();
    site.url = ref
    site.put()
    visits = MyVisit()
    visits.site = site
    visits.put()
  else:
    site = site[0]
    site.last_access = datetime.now();
    site.views = site.views + 1;
    site.put()
    data = memcache.get(hash)
    if data is None:
      memcache.add(key=hash, value=1 , time=86400);
    visits = search_visists(site);
    if (not visits):
      visits = MyVisit()
      visits.site = site
      visits.put()
    else:
      visits = visits[0];
      if (data is None):
        visits.vis = visits.vis+1;
      visits.imp = visits.imp+1;
      visits.put()

def searchsite(ref):
  return MySite.all().filter('url =', ref).fetch(1)

def search_visists(site, all=0):
  v = MyVisit.all()
  v.filter('site =', site)
  v.order('-date')
  if (all == 0):
    tt = datetime.today()
    td = datetime(tt.year, tt.month, tt.day)
    v.filter("date =", td)
  return v.fetch(100)
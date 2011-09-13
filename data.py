import logging

from datetime import datetime
from google.appengine.api import memcache
from google.appengine.ext import db


__author__ = "aquilax"
__date__ = "$Feb 20, 2010 8:15:35 AM$"


class MySite(db.Model):
  url = db.StringProperty(verbose_name="Url")
  created = db.DateTimeProperty(verbose_name="Added", auto_now_add=True)
  views = db.IntegerProperty(default=1)
  last_access = db.DateTimeProperty(verbose_name="Last accessed", auto_now_add=True)

class MyVisit(db.Model):
  site = db.ReferenceProperty(MySite)
  vis = db.IntegerProperty(default=1)
  imp = db.IntegerProperty(default=1)
  date = db.DateProperty(auto_now_add=True)

#def save(ref, ip):
#  if (ref is None):
#    return
#  site = searchsite(ref)
#  hash = ref + "|" + ip;
#  if (not site):
#    memcache.add(key=hash, value=1, time=86400);
#    site = MySite();
#    site.url = ref
#    site.put()
#    visits = MyVisit()
#    visits.site = site
#    visits.put()
#  else:
#    site.last_access = datetime.now();
#    site.views = site.views + 1;
#    site.put()
#    data = memcache.get(hash)
#    if data is None:
#      memcache.add(key=hash, value=1, time=86400);
#    visits = search_visists(site);
#    if (not visits):
#      visits = MyVisit()
#      visits.site = site
#      visits.put()
#    else:
#      visits = visits[0];
#      if (data is None):
#        visits.vis = visits.vis + 1;
#      visits.imp = visits.imp + 1;
#      visits.put()

def save(ref, ip):
  if (ref is None):
    return
  # sum www-s
  if ref.startswith('www.'):
    ref = ref[4:]
  site = searchsite(ref)
  hash = ref + "|" + ip;
  if (not site):
    memcache.add(key=hash, value=1, time=86400);
    site = MySite();
    site.url = ref
    site.put()
    visits = MyVisit()
    visits.site = site
    visits.put()
  else:
    imp = 1
    vis = 0
    data = memcache.get(hash)
    if data is None:
      memcache.add(key=hash, value=1, time=86400);
      vis = 1
    increment_multi_counter(site.key().id(), vis, imp)

def searchsite(ref):
  hash = 'ref:' + ref;
  id = memcache.get(hash);
  if (id):
    return MySite.get_by_id(id)
  else:
    site = MySite.all().filter('url =', ref).fetch(1)
    if (site):
      site = site[0]
      id = site.key().id()
      memcache.add(key=hash, value=id)
    return site;

def search_visists(site, all=0):
  v = MyVisit.all()
  v.filter('site =', site)
  v.order('-date')
  if (all == 0):
    tt = datetime.today()
    td = datetime(tt.year, tt.month, tt.day)
    v.filter("date =", td)
  return v.fetch(60)


def pack_counts(a, b, c, d):
  """Packs a, b, c, d into one 64-bit long (as 4 16-bit ints).  Assumes each
    is in the range [0, 2**16-1]."""
  return (a << 0) + (b << 16) + (c << 32) + (d << 48)

def unpack_counts(t):
  """Unpacks 4 16-bit values from t."""
  a = t & 0xFFFF
  b = (t >> 16) & 0xFFFF
  c = (t >> 32) & 0xFFFF
  d = t >> 48
  return (a, b, c, d)

def update(key, vis, imp):
  site = MySite.get_by_id(key)
  site.views = site.views + imp;
  site.last_access = datetime.now();
  site.put()
  visits = search_visists(site)
  if (not visits):
    visits = MyVisit()
    visits.site = site
    visits.put()
  else:
    visits = visits[0];
    visits.vis = visits.vis + vis;
    visits.imp = visits.imp + imp;
    visits.put()


def increment_multi_counter(key='nil', vis=0, imp=0, update_interval=60):
  """Increments the memcache counter for the specified cumulative contribution
    for the specified race and/or user.
    Args:
      race_id: the race this contribution is for
      user_id: the user this contribution is for
      delta: Non-negative integer value (int or long) to increment key by, defaulting to 1.
      update_interval: Minimum interval between updates.
    """
  lock_key  = "ctr_L:%s" % (key, )
  counts_key = "ctr_V:%s" % (key, )

  delta = pack_counts(vis, imp, 0, 0)
  if memcache.add(lock_key, None, time=update_interval):
    # time to update the DB
    prev_packed_counts = int(memcache.get(counts_key) or 0)
    new_counts = unpack_counts(prev_packed_counts + delta)

    def tx():
      vis = new_counts[0]
      imp = new_counts[1]
      update(key, vis, imp)
    try:
      tx();
      #db.run_in_transaction(tx)
      if prev_packed_counts > 0 and memcache.decr(counts_key, delta=prev_packed_counts) is None:
        logging.warn("counter %s could not be decremented (will double-count): %s" % (key, unpack_counts(prev_packed_counts)))
    except db.Error:
      # db failed to update: we'll try again later; just add delta to memcache like usual for now
      logging.error(db.Error);
      memcache.incr_async(counts_key, delta, initial_value=0)
  else:
    # Just update memcache
    memcache.incr_async(counts_key, delta, initial_value=0)

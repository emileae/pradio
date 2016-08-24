from google.appengine.ext import ndb
# from google.appengine.api import taskqueue

import utils

# ================================
#  Podradio stuff
# ================================

class InAppMessage(ndb.Model):
    message = ndb.StringProperty()
    link = ndb.StringProperty()
    image = ndb.StringProperty()
    media_key = ndb.KeyProperty(kind="Media")
    region = ndb.KeyProperty(kind="Region", default=None)
    created = ndb.DateTimeProperty(auto_now_add=True)

class Registration(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    schools = ndb.KeyProperty(kind="School", repeated=True)
    school_names = ndb.StringProperty(repeated=True)
    school_other = ndb.StringProperty()
    subscribed = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

class Podcast(ndb.Model):
    title = ndb.StringProperty()
    description = ndb.TextProperty()
    set_date = ndb.StringProperty()
    audio_key = ndb.KeyProperty(kind="Audio")
    download_link = ndb.StringProperty()
    share_url = ndb.StringProperty(default="http://www.podradio.co.za")
    school = ndb.KeyProperty(kind="School")
    region = ndb.KeyProperty(kind="Region")
    downloads = ndb.IntegerProperty(default=0)
    plays = ndb.IntegerProperty(default=0)
    created = ndb.DateTimeProperty(auto_now_add=True)

class School(ndb.Model):
    name = ndb.StringProperty()
    image = ndb.StringProperty(default="img/podradio-logo.png")
    media_key = ndb.KeyProperty(kind="Media")
    region = ndb.KeyProperty(kind="Region")
    active = ndb.BooleanProperty(default=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

class Region(ndb.Model):
    name = ndb.StringProperty()
    active = ndb.BooleanProperty(default=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

class Counter(ndb.Model):
    podcast_downloads = ndb.IntegerProperty(default=0)
    podcast_plays = ndb.IntegerProperty(default=0)
    registrations = ndb.IntegerProperty(default=0)
    created = ndb.DateTimeProperty(auto_now_add=True)


# ================================
#  Settings
# ================================

class Settings(ndb.Model):
    ads = ndb.BooleanProperty(default=True)
    top_ads = ndb.BooleanProperty(default=True)
    mid_ads = ndb.BooleanProperty(default=True)
    bottom_ads = ndb.BooleanProperty(default=True)
    share_btns = ndb.BooleanProperty(default=True)
    donate_btns = ndb.BooleanProperty(default=True)

    articles = ndb.BooleanProperty(default=False)
    crosswords = ndb.BooleanProperty(default=False)
    quizzes = ndb.BooleanProperty(default=False)

    created = ndb.DateTimeProperty(auto_now_add=True)


# ================================
#  Media
# ================================
class Media(ndb.Model):
    gcs_filename = ndb.StringProperty(default = None)
    serving_url = ndb.StringProperty(default = None)
    type = ndb.StringProperty()
    type_id = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

class Audio(ndb.Model):
    gcs_filename = ndb.StringProperty(default = None)
    created = ndb.DateTimeProperty(auto_now_add=True)


# ================================
#  Share / Contact
# ================================

class EmailShare(ndb.Model):
    from_email = ndb.StringProperty()
    to_email = ndb.StringProperty()
    share_url = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

class Subscriber(ndb.Model):
    email = ndb.StringProperty()
    name = ndb.StringProperty()
    crossword = ndb.BooleanProperty(default=True)
    article = ndb.BooleanProperty(default=True)
    quiz = ndb.BooleanProperty(default=True)
    active = ndb.BooleanProperty(default=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    
class Contact(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    message = ndb.TextProperty()
    contact_type = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    
    

    

import re
import hashlib
import hmac
import random
import string
from string import letters
import logging
import json
import time

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.api import mail
from google.appengine.api import app_identity

import cloudstorage as gcs

#for mandrill api
from google.appengine.api import urlfetch

import model

# http://img.youtube.com/vi/7MLWHGRnqfI/0.jpg youtube image link

secret = 'p0Dr4d1o'
sender_email = "podradiocoza@gmail.com"
mandrill_key = "IF-d1gvp1NsY4AwbDS4OPA"
app_id = app_identity.get_application_id()


# ---------- user auth stuff
#PW HASHING
def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)
    
def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))
    
# returns a cookie with a value value|hashedvalue
def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())
# returns the origional value and validates if given hashed cookie matches our hash of the value    
def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val
        
def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


#REGEX for register validtion
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return email and EMAIL_RE.match(email)

def update_counter(count_type):
    counter = model.Counter.query().get()

    if count_type == "registration":
        if not counter:
            counter = model.Counter(registrations=1)
            counter.put()
        else:
            counter.registrations += 1
            counter.put()

    if count_type == "download":
        if not counter:
            counter = model.Counter(podcast_downloads=1)
            counter.put()
        else:
            counter.podcast_downloads += 1
            counter.put()

    if count_type == "play":
        if not counter:
            counter = model.Counter(podcast_plays=1)
            counter.put()
        else:
            counter.podcast_plays += 1
            counter.put()


# =============================
# Google Cloud Storage
# =============================
# http://storage.googleapis.com/<bucket name>/<object name>
# grant access to AllUsers as a group - Bucket
# grant acc to AllUsers as a group for default object permissions
# comparison between serve adn direct from GCS: http://audio-test.appspot.com

def save_gcs_to_media(gcs_filename, serving_url):
    media = model.Media(gcs_filename=gcs_filename, serving_url=serving_url)
    media.put()
    return media

def save_gcs_to_audio(gcs_filename):
    audio = model.Audio(gcs_filename=gcs_filename)
    audio.put()
    return audio

def delete_audio_from_gcs(gcs_filename):
    if gcs_filename:
        gcs.delete(gcs_filename[3:])


def delete_media(gcs_filename):
    images.delete_serving_url(blobstore.create_gs_key(gcs_filename))
    gcs.delete(gcs_filename[3:])
    return True

def delete_from_gcs(gcs_filename):
    if gcs_filename:
        images.delete_serving_url(blobstore.create_gs_key(gcs_filename))
        gcs.delete(gcs_filename[3:])

def save_to_gcs(file_obj):
    serving_url = ''#just assign it adn reassign later

    time_stamp = int(time.time())
    app_id = app_identity.get_application_id()

    fname = '/%s.appspot.com/post_%s.jpg' % (app_id, time_stamp)
    logging.error(fname)

    # Content Types
    # audio/mpeg
    # image/jpeg

    gcs_file = gcs.open(fname, 'w', content_type="image/jpeg")
    gcs_file.write(file_obj)
    gcs_file.close()

    gcs_filename = "/gs%s" % fname
    serving_url = images.get_serving_url(blobstore.create_gs_key(gcs_filename))
    media_obj = save_gcs_to_media(gcs_filename, serving_url)

    return media_obj

def upload_image(image):
    media_obj = save_to_gcs(image)

    json_obj = {
        "message":"success",
        "media_id": media_obj.key.id(),
        "post_id": post.key.id()
        }

    return json_obj

def upload_mp3(audio_file):
    time_stamp = int(time.time())
    app_id = app_identity.get_application_id()
    fname = '/%s.appspot.com/post_%s_%s.mp3' % (app_id, "audio_file", time_stamp)
    # logging.error(fname)

    # Content Types
    # audio/mpeg
    # image/jpeg

    gcs_file = gcs.open(fname, 'w', content_type="audio/mpeg")
    gcs_file.write(audio_file)
    gcs_file.close()

    gcs_filename = "/gs%s" % fname
    audio_obj = save_gcs_to_audio(gcs_filename)

    return audio_obj









#-------- create a user

def create_user(type, name, description, profile_img, gcs_filename, email, website):

    if valid_email(email):
        password = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(8))
        pw_hash = make_pw_hash(email, password)
        logging.error("------------------ type:%s " % type)
        user = model.User(
            parent=model.users_key(), 
            type=type, 
            name=name, 
            description=description, 
            profile_img=profile_img, 
            gcs_filename=gcs_filename, 
            email=email, 
            website=website,
            temp_pw=password,
            pw_hash=pw_hash)
        user.put()

        return user

    else:
        return False























def request_blob_url(self, callback_url, max_bytes):
    upload_url = blobstore.create_upload_url(callback_url, max_bytes)
    return upload_url
    
def send_gmail(email, subject, body):
    try:
        logging.error("sending subscription mail")
        message = mail.EmailMessage(sender="Hollow Fish <%s>" % sender_email,
                                subject=subject)
        message.to = email
        message.html = body
        message.send()
    except:
        logging.error("couldnt send gmail... probably invalid email")




#saving blobkey to seller obj along with serving url
def save_blob_to_image_obj(blob_key, price, title, description):
    img_url = images.get_serving_url(blob_key)
    portfolio_image = model.Images(img_url=img_url, img_key=blob_key, price=price, title=title, description=description)
    portfolio_image.put()
    return img_url

def send_mandrill_mail(subject, html, text, email_list, inline_css):
    
    url = "https://mandrillapp.com/api/1.0/messages/send.json"

    logging.error("email list")
    logging.error(email_list)

    form_json = {
            "key": mandrill_key,
            "message": {
                "html": html,
                "text": text,
                "subject": subject,
                "from_email": sender_email,
                "from_name": "One Two Happy",
                "to": email_list,
                "headers": {
                    "Reply-To": sender_email
                },
                "important": False,
                "track_opens": True,
                "track_clicks": True,
                "auto_text": None,
                "auto_html": None,
                "inline_css": inline_css,
                "url_strip_qs": None,
                "preserve_recipients": False,
                "view_content_link": None,
                "bcc_address": None,
                "tracking_domain": None,
                "signing_domain": None,
            },
            "async": False,
            "ip_pool": "Main Pool",
            "send_at": None
        }
    

    result = urlfetch.fetch(url=url, payload=json.dumps(form_json), method=urlfetch.POST)

    logging.error("MANDRILL RESULT")

    logging.error(dir(result))
    logging.error(result.status_code)
    logging.error(json.loads(result.content))

def send_mandrill_confirmation_mail(subject, html, text, to_email, from_email, inline_css):
    
    url = "https://mandrillapp.com/api/1.0/messages/send.json"

    form_json = {
            "key": mandrill_key,
            "message": {
                "html": html,
                "text": text,
                "subject": subject,
                "from_email": from_email,
                "from_name": "Podradio",
                "to": [{
                    "email": to_email,
                    "name": "",
                    "type": "to"
                }],
                "headers": {
                    "Reply-To": from_email
                },
                "important": False,
                "track_opens": True,
                "track_clicks": True,
                "auto_text": None,
                "auto_html": None,
                "inline_css": inline_css,
                "url_strip_qs": None,
                "preserve_recipients": False,
                "view_content_link": None,
                "bcc_address": None,
                "tracking_domain": None,
                "signing_domain": None,
            },
            "async": False,
            "ip_pool": "Main Pool",
            "send_at": None
        }
    

    result = urlfetch.fetch(url=url, payload=json.dumps(form_json), method=urlfetch.POST)

    logging.error("MANDRILL RESULT")

    logging.error(dir(result))
    logging.error(result.status_code)
    logging.error(json.loads(result.content))
    
    
    
    
    
    
    
    
    
    
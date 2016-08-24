#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import logging
import os
from string import letters
import json
from datetime import datetime, timedelta
import datetime
import time
import urllib
import re
import csv
import random
from collections import OrderedDict

from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import mail
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api import taskqueue

import model
import utils

import cloudstorage as gcs

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

cookie_name = "za.co.podradio"

def check_none(value):
    if not value:
        return ""
    else:
        return value
jinja_env.filters['check_none'] = check_none

def blog_date(value):
    return value.strftime("%d/%m/%y")
jinja_env.filters['blog_date'] = blog_date

def replace_space(value):
    return value.replace(" ", "_")
jinja_env.filters['replace_space'] = replace_space

class MainHandler(webapp2.RequestHandler):

#TEMPLATE FUNCTIONS    
    def write(self, *a, **kw):
        self.response.headers['Host'] = 'localhost'
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(*a, **kw)
        
    def render_str(self, template, **params):
        #params['user'] = self.user
        #params['buyer'] = self.buyer
        t = jinja_env.get_template(template)
        return t.render(params)
        
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    #JSON rendering
    def render_json(self, obj):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.headers['Host'] = 'localhost'
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.out.write(json.dumps(obj))
   
    #COOKIE FUNCTIONS
    # sets a cookie in the header with name, val , Set-Cookie and the Path---not blog    
    # def set_secure_cookie(self, name, val):
    #     cookie_val = utils.make_secure_val(val)
    #     self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))# consider imcluding an expire time in cookie(now it closes with browser), see docs
    # # reads the cookie from the request and then checks to see if its true/secure(fits our hmac)    
    # def read_secure_cookie(self, name):
    #     cookie_val = self.request.cookies.get(name)
    #     if cookie_val:
    #         cookie_val = urllib.unquote(cookie_val)
    #     return cookie_val and utils.check_secure_val(cookie_val)
    
    # def login(self, user):
    #     self.set_secure_cookie(cookie_name, str(user.key.id()))

    # def logout(self):
    #     self.response.headers.add_header('Set-Cookie', '%s=; Path=/' % cookie_name)
    
    # def initialize(self, *a, **kw):
    #     webapp2.RequestHandler.initialize(self, *a, **kw)
    #     uid = self.read_secure_cookie(cookie_name)

    #     # settings = model.Settings.query().get()
    #     # self.settings = settings

    #     self.user = uid and model.User.by_id(int(uid))
        

# ===================================
# Public Pages - Main
# ===================================


class Home(MainHandler):
    def get(self):
        year = datetime.datetime.now().year
        self.render('index.html', year=year)

class Registration(MainHandler):
    def get(self):
        email = self.request.get("email")
        name = self.request.get("name")

        school_ids = []

        if email:
            user = model.Registration.query(model.Registration.email == email).get()
            name = user.name
            email = user.email
            schools = user.schools
            for s in schools:
                school_ids.append(s.id())

        regions = model.Region.query(model.Region.active == True).order(model.Region.name).fetch()

        school_dict = OrderedDict()

        for r in regions:
            school_dict[r.name] = []

        schools = model.School.query().order(model.School.name).fetch()

        for s in schools:
            region = s.region.get().name
            school_dict[region].append(s)

        error = self.request.get("error")

        self.render("registration-confirm.html", school_dict=school_dict, schools=schools, name=name, email=email, error=error, school_ids=school_ids)

    def post(self):
        email = self.request.get("email")
        name = self.request.get("name")
        schools = self.request.get_all("school")

        school_list = []
        school_list_names = []
        for s in schools:
            school = model.School.get_by_id(int(s))
            school_list.append(school.key)
            school_list_names.append(school.name)

        user = model.Registration.query(model.Registration.email == email).get()

        logging.error("schools:  %s" % schools)
        logging.error("school_list:  %s" % school_list)

        if user:
            if name:
                user.name = name
            if schools:
                user.schools = school_list
                user.school_names = school_list_names

            user.put()

            self.render("registration-thank-you.html")

        else:
            registration = model.Registration( name=name, email=email, schools=school_list, school_names=school_list_names, subscribed="yes" )
            registration.put()
            self.render("registration-thank-you.html")
            #error = "no user was found with the email address: %s <br> please confirm the email address that you used to register with Podradio." % email
            #self.redirect("/registration?email=%s&name=%s&error=%s" % ( email, name, error ))

class Privacy(MainHandler):
    def get(self):
        self.render("privacy.html")

# ===================================
# Mobile API
# ===================================

class APIGetRegionList(MainHandler):
    def get(self):
        regions = model.Region.query(model.Region.active == True).order(model.Region.name).fetch()

        region_list = []

        for region in regions:
            name = region.name

            region_obj = {
                "name": name,
                "id": region.key.id()
            }

            region_list.append(region_obj)

        self.render_json(region_list)

class APIGetSchoolList(MainHandler):
    def get(self, region_id):
        region = model.Region.get_by_id(int(region_id))

        schools = model.School.query(model.School.region == region.key, model.School.active == True).order(model.School.name).fetch()

        school_list = []

        for school in schools:
            name = school.name

            school_obj = {
                "name": name,
                "id": school.key.id(),
                "image": school.image
            }

            school_list.append(school_obj)

        self.render_json(school_list)

class APIGetMessage(MainHandler):
    def get(self):

        podcast_id = self.request.get("podcast_id")

        podcast = model.Podcast.get_by_id(int(podcast_id))
        school = podcast.school.get()
        region = school.region

        # logging.error("....................c c c c c c ")
        # logging.error(region)

        message = model.InAppMessage.query(model.InAppMessage.region == region).get()
        logging.error(message)
        if not message:
            message = model.InAppMessage.query(model.InAppMessage.region == None).get()

        if message:
            message_text = message.message
            link = message.link
            image = message.image
        else:
            message_text = ""
            link = False
            image = "img/podradio-logo.png"

        self.render_json({
            "message": message_text,
            "link": link,
            "image": image
            })

class APIRegister(MainHandler):
    def post(self):
        name = self.request.get("name")
        email = self.request.get("email")
        subscribed = self.request.get("subscribed")

        registration = model.Registration.query(model.Registration.email == email).get()

        if not registration:
            registration = model.Registration( name=name, email=email, subscribed=subscribed )
            registration.put()

            utils.update_counter("registration")

            #html = """ Please visit this <a href="http://podradio-za.appspot.com/registration?email=%s&name=%s" target="_blank">link</a> to confirm your registration with podardio.<br> If this email isn't displaying properly, please, copy paste the following link into your browser:<br><br> http://podradio-za.appspot.com/registration?email=%s&name=%s """ % (email, name, email, name)

            # html = """ Welcome to Podradio and thank you for downloading our app.<br><br>Please can you click on <a href="http://podradio-za.appspot.com/registration?email=%s&name=%s" target="_blank">this link</a> to indicate which school/schools you are interested in listening to.<br><br>Thank you<br>Podradio<br><br><br>If this email isn't displaying properly, please, copy paste the following link into your browser:<br><br> http://podradio-za.appspot.com/registration?email=%s&name=%s  """ % (email, name, email, name)

            # text = """ If this email isn't displaying properly, please, copy paste the following link into your browser: http://podradio-za.appspot.com/registration?email=%s&name=%s """

            html = """
            <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
            <html>
                <head>
                    <title>Podradio welcome!</title>
                </head>
                <body>
                    <p>Welcome to Podradio and thank you for downloading our app.
                    <br><br>Please visit <a href="http://podradio-za.appspot.com/registration?email=%s&amp;name=%s" target="_blank">this link</a> to indicate which school/schools you are interested in listening to.
                    <br><br>Thank you<br>Podradio<br><br><br>
                    If this email isn't displaying properly, please, copy paste the following link into your browser:
                    <br><br> http://podradio-za.appspot.com/registration?email=%s&amp;name=%s
                    </p>
                </body>
            </html> 

            """ % (email, name, email, name)

            text = """Welcome to Podradio, Please visit http://podradio-za.appspot.com/registration?email=%s&amp;name=%s to indicate which school/schools you are interested in listening to.""" % (email, name)

            utils.send_mandrill_confirmation_mail("Podradio Confirmation", html, text, email, 'podradiocoza@gmail.com', False)


        else:
            registration.name = name
            registration.subscribed = subscribed
            registration.put()

        self.render_json({
            "message": "success",
            "registration_id": registration.key.id(),
            "email": email,
            "name": name,
            "subscribed": subscribed
        })

class APIGetPodcasts(MainHandler):
    def get(self):
        # school_id = self.request.get("school_id")
        # if school_id:
        #     school = model.School.get_by_id(int(school_id))

        podcasts = model.Podcast.query().order(-model.Podcast.created).fetch()

        bucket_name = "%s.appspot.com" % utils.app_id

        podcast_list = []

        for p in podcasts:
            download_link = "http://" + bucket_name + p.download_link
            title = p.title
            description = p.description
            podcast_obj = {
                "title": title,
                "description": description,
                "download_link": download_link,
                "id": p.key.id()
            }

            podcast_list.append(podcast_obj)

        podcast_json = {
            "podcasts": podcast_list
        }

        self.render_json(podcast_json)


class APIGetSchoolPodcasts(MainHandler):
    def get(self, school_id):
        school = model.School.get_by_id(int(school_id))

        # podcasts = model.Podcast.query(model.Podcast.school == school.key).order(-model.Podcast.created).fetch()

        curs = Cursor(urlsafe=self.request.get('cursor'))
        podcasts, next_curs, more = model.Podcast.query(model.Podcast.school == school.key).order(-model.Podcast.created).fetch_page(60, start_cursor=curs)
        
        if more and next_curs:
            next_curs = next_curs.urlsafe()
        else:
            next_curs = False


        podcast_list = []

        for podcast in podcasts:
            title = podcast.title
            description = podcast.description
            download_link = podcast.download_link

            podcast_obj = {
                "title": title,
                "description": description,
                "download_link": download_link,
                "id": podcast.key.id(),
                "share_url": podcast.share_url,
                "date": podcast.created.strftime("%d-%m-%Y"),
                "school": school.name,
                "image": school.image
            }

            podcast_list.append(podcast_obj)

        self.render_json({
            "podcasts":podcast_list,
            "next_curs": next_curs
            })

class APITrackDownload(MainHandler):
    def post(self):
        podcast_id = self.request.get("podcast_id")
        podcast = model.Podcast.get_by_id(int(podcast_id))
        if podcast:
            if podcast.downloads:
                podcast.downloads += 1
            else:
                podcast.downloads = 1
            podcast.put()
        utils.update_counter("download")

class APITrackPlay(MainHandler):
    def post(self):
        podcast_id = self.request.get("podcast_id")
        podcast = model.Podcast.get_by_id(int(podcast_id))
        if podcast:
            if podcast.plays:
                podcast.plays += 1
            else:
                podcast.plays = 1
            podcast.put()
        utils.update_counter("play")


# ===================================
# Quiz List
# ===================================


class Admin(MainHandler):
    def get(self):
        counter = model.Counter.query().get()
        self.render('cms.html', counter=counter)

class AdminAddPodcast(MainHandler):
    def get(self, school_id):
        school = model.School.get_by_id(int(school_id))

        podcast_id = self.request.get("podcast_id")
        if podcast_id:
            podcast = model.Podcast.get_by_id(int(podcast_id))
        else:
            podcast = None

        podcasts = model.Podcast.query(model.Podcast.school == school.key).fetch()


        self.render("admin-add-podcast.html", school=school, podcast=podcast, podcasts=podcasts)

    def post(self, school_id):
        school = model.School.get_by_id(int(school_id))
        title = self.request.get("title")
        description = self.request.get("description")
        audio = self.request.get("audio")
        share_url = self.request.get("share_url")
        podcast_id = self.request.get("podcast_id")

        if podcast_id:
            podcast = model.Podcast.get_by_id(int(podcast_id))

            if audio:
                audio_obj = utils.upload_mp3(audio)

                old_audio_obj = podcast.audio_key.get()
                if old_audio_obj:
                    utils.delete_audio_from_gcs(old_audio_obj.gcs_filename)

                podcast.audio_key = audio_obj.key
                podcast.download_link = "http://storage.googleapis.com%s" % audio_obj.gcs_filename[3:]

            podcast.title=title
            podcast.description = description
            podcast.share_url = share_url

            podcast.put()

            self.redirect("/admin/add_podcast/%s?podcast_id=%s" % ( school_id, podcast_id))

        else:
            if audio:
                logging.error("New audio upload")
                audio_obj = utils.upload_mp3(audio)

            if title and description and audio_obj and school:
                download_link = "http://storage.googleapis.com%s" % audio_obj.gcs_filename[3:]
                podcast = model.Podcast(title=title, description=description, audio_key=audio_obj.key, download_link=download_link, school=school.key, share_url=share_url)
                podcast.put()

            self.redirect("/admin/add_podcast/%s" % school_id)
        # self.redirect("http://storage.googleapis.com/%s.appspot.com/%s" % ( utils.app_id, audio_obj ))

class AdminDeletePodcast(MainHandler):
    def post(self):
        delete_id = self.request.get("delete_id")

        podcast = model.Podcast.get_by_id(int(delete_id))

        school_id = podcast.school.id()

        # delete audio file
        utils.delete_from_gcs(podcast.audio_key.get().gcs_filename)
        podcast.audio_key.delete()

        podcast.key.delete()

        self.redirect("/admin/add_podcast/%s" % school_id)


class AdminAddRegion(MainHandler):
    def get(self):
        region_id = self.request.get("region_id")
        region = None
        if region_id:
            region = model.Region.get_by_id(int(region_id))

        regions = model.Region.query(model.Region.active == True).fetch()

        self.render("admin-add-region.html", regions=regions, region=region)

    def post(self):
        name = self.request.get("name")
        
        existing = model.Region.query(model.Region.name == name).get()

        if not existing:
            region = model.Region(name=name)
            region.put()

        self.redirect("/admin/add_region")

class AdminDeleteRegion(MainHandler):
    def post(self):
        delete_id = self.request.get("delete_id")
        region = model.Region.get_by_id(int(delete_id))
        region.active = False
        region.put()

        self.redirect("/admin/add_region")

class AdminAddSchool(MainHandler):
    def get(self, region_id):

        school_id = self.request.get("school_id")

        school = None
        if school_id:
            school = model.School.get_by_id(int(school_id))

        region = model.Region.get_by_id(int(region_id))
        schools = model.School.query(model.School.region == region.key, model.School.active == True).fetch()

        self.render("admin-add-school.html", region=region, schools=schools, school=school)

    def post(self, region_id):
        name = self.request.get("name")
        region = model.Region.get_by_id(int(region_id))
        image = self.request.get("image")
        
        school_id = self.request.get("school_id")

        logging.error("SAVE SCHOOL")

        if school_id:

            logging.error("SCHOOL ID")

            school = model.School.get_by_id(int(school_id))
            if image:
                media_obj = utils.save_to_gcs(image)
                old_media_obj = school.media_key.get()
                if old_media_obj:
                    utils.delete_from_gcs(old_media_obj.gcs_filename)
                    old_media_obj.key.delete()

                school.image = media_obj.serving_url
                school.media_key = media_obj.key
                school.put()

            school.name=name
            school.put()

            self.redirect( "/admin/add_school/%s?school_id=%s" % ( region_id, school_id ) )

        else:

            logging.error("NO SCHOOL ID")

            if name and region:
                school = model.School.query(model.School.name == name, model.School.region == region.key).get()

                if not school:
                    school = model.School(name=name, region=region.key)
                    school.put()

                if school and image:
                    media_obj = utils.save_to_gcs(image)
                    school.image = media_obj.serving_url
                    school.media_key = media_obj.key
                    school.put()

            self.redirect("/admin/add_school/%s" % region_id)

class AdminDeleteSchool(MainHandler):
    def post(self):
        delete_id = self.request.get("delete_id")
        school = model.School.get_by_id(int(delete_id))
        school.active = False
        region_id = school.region.id()
        school.put()

        self.redirect("/admin/add_school/%s" % region_id)

class AdminInAppMessage(MainHandler):
    def get(self):
        regions = model.Region.query().fetch()
        messages = model.InAppMessage.query().fetch()

        self.render("admin-in-app-message.html", messages=messages, regions=regions)

    def post(self):
        message_id = self.request.get("message_id")
        message_text = self.request.get("message")
        sponsor_link = self.request.get("link")
        image = self.request.get("image")
        region = self.request.get("region")

        delete_message = self.request.get("delete_message")

        if delete_message:
            message = model.InAppMessage.get_by_id(int(delete_message))
            message.key.delete()
        else:
            region_key = None
            if region:
                region = model.Region.get_by_id(int(region))
                region_key = region.key

            remove_image = self.request.get("remove_image")

            message = None
            if message_id:
                message = model.InAppMessage.get_by_id(int(message_id))

            if remove_image == "yes" and message.image:
                if message.image and message.media_key:
                    utils.delete_from_gcs(message.media_key.get().gcs_filename)
                    message.media_key.delete()
                message.image = ""
                message.put()

            if message:
                if image:
                    media_obj = utils.save_to_gcs(image)
                    if message.image and message.media_key:
                        utils.delete_from_gcs(message.media_key.get().gcs_filename)
                        message.media_key.delete()
                    message.image = media_obj.serving_url
                    message.media_key = media_obj.key

                message.message = message_text
                message.link = sponsor_link
                message.region = region_key
                message.put()
            else:
                if image:
                    media_obj = utils.save_to_gcs(image)
                    message = model.InAppMessage(message=message_text, link=sponsor_link, image=media_obj.serving_url, media_key=media_obj.key, region=region_key)
                else:
                    message = model.InAppMessage(message=message_text, link=sponsor_link, region=region_key)
                message.put()

        self.redirect("/admin/in_app_message")

class AdminEmails(MainHandler):
    def get(self):
        page = self.request.get("page")
        if not page:
            page = 1
        else:
            page = int(page) + 1

        curs = Cursor(urlsafe=self.request.get('cursor'))
        registrations, next_curs, more = model.Registration.query().order(-model.Registration.created).fetch_page(300, start_cursor=curs)
        
        if more and next_curs:
            next_curs = next_curs.urlsafe()
        else:
            next_curs = False

        self.render("admin-emails.html", registrations=registrations, next_curs=next_curs, page=page)

class AdminEmailsCSV(MainHandler):
    def get(self):
        page = self.request.get("page")
        if not page:
            page = 1
        curs = Cursor(urlsafe=self.request.get('cursor'))
        registrations, next_curs, more = model.Registration.query().order(-model.Registration.created).fetch_page(300, start_cursor=curs)
        
        if more and next_curs:
            next_curs = next_curs.urlsafe()
        else:
            next_curs = False

        self.response.headers['Content-Type'] = 'text/csv'
        self.response.headers['Content-Disposition'] = 'attachment; filename=podradio_emails_%s.csv' % str(page)
        writer = csv.writer(self.response.out)

        writer.writerow([
            'Page %s' % page, 
            ])

        writer.writerow([
            'Name', 
            'Email',
            "Date",
            'Subscribed',
            'Schools'
            ])
        for r in registrations:
            school_list = ""
            for s in r.school_names:
                s = unicode(s).encode("utf-8")# re.sub(r'[^\x00-\x7F]+','-', s)
                school_list += s+"/"


            # self.writer.writerow([unicode(s).encode("utf-8") for s in row])
            name = unicode(r.name).encode("utf-8")# re.sub(r'[^\x00-\x7F]+','-', r.name)
            email = unicode(r.email).encode("utf-8")# re.sub(r'[^\x00-\x7F]+','-', r.email)
            date = r.created.strftime("%d/%m/%y %H:%M")
            writer.writerow([
                name,
                email,
                date,
                r.subscribed,
                school_list
                ])
            # writer.writerow([
            #     r.name,
            #     r.email,
            #     r.subscribed,
            #     school_list
            #     ])

class AdminSEO(MainHandler):
    def get(self):
        obj_id = self.request.get("obj_id")
        obj_kind = self.request.get("obj_kind")

        obj = utils.query_by_kind_id(obj_id, obj_kind)

        self.render("seo-form.html", obj=obj)

    def post(self):
        seo_title = self.request.get("seo_title")
        seo_description = self.request.get("seo_description")
        seo_tags = self.request.get("seo_tags")

        obj_id = self.request.get("obj_id")
        obj_kind = self.request.get("obj_kind")

        obj = utils.query_by_kind_id(obj_id, obj_kind)

        if obj:
            obj.seo_title = seo_title
            obj.seo_description = seo_description
            
            tags = seo_tags.replace(" ", "_")
            tags = re.sub('[^0-9a-zA-Z,]+', '', tags)
            tags = tags.lower()
            seo_tags = tags.split(",")
            seo_tags = filter(None, seo_tags)

            obj.seo_keywords = seo_tags
            # utils.index_keywords(seo_tags, obj_id, obj_kind) # this is more like tagging adn should be dealt with differently than seo keywords
            obj.put()

        self.redirect("/admin/seo?obj_id=%s&obj_kind=%s" % (obj_id, obj_kind))

class AdminSettings(MainHandler):
    def get(self):
        settings = model.Settings.query().get()

        self.render("settings.html", settings=settings)

    def post(self):
        ads = self.request.get("ads")
        top_ads = self.request.get("top_ads")
        mid_ads = self.request.get("mid_ads")
        bottom_ads = self.request.get("bottom_ads")

        settings = model.Settings.query().get()

        if ads:
            ads = True
        else:
            ads = False
        
        if top_ads:
            top_ads = True
        else:
            top_ads = False
        
        if mid_ads:
            mid_ads = True
        else:
            mid_ads = False
        
        if bottom_ads:
            bottom_ads = True
        else:
            bottom_ads = False

        if not settings:
            settings = model.Settings(ads=ads, top_ads=top_ads, mid_ads=mid_ads, bottom_ads=bottom_ads)
            settings.put()
        else:
            settings.ads=ads
            settings.top_ads=top_ads
            settings.mid_ads=mid_ads
            settings.bottom_ads=bottom_ads
            settings.put()

        self.redirect("/admin/settings")

class AdminRefreshData(MainHandler):
    def get(self):
        regions = model.Region.query().fetch()

        for r in regions:
            r.active = True
            r.put()

        schools = model.School.query().fetch()

        for s in schools:
            s.active = True
            s.put()

        self.response.out.write("done...")

class TestEmail(MainHandler):
    def get(self):
        email = "emile.esterhuizen@gmail.com"
        name = "Emile"
        html = """
            <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
            <html>
                <head>
                    <title>Podradio welcome!</title>
                </head>
                <body>
                    <p>Welcome to Podradio and thank you for downloading our app.
                    <br><br>Please visit <a href="http://podradio-za.appspot.com/registration?email=%s&amp;name=%s" target="_blank">this link</a> to indicate which school/schools you are interested in listening to.
                    <br><br>Thank you<br>Podradio<br><br><br>
                    If this email isn't displaying properly, please, copy paste the following link into your browser:
                    <br><br> http://podradio-za.appspot.com/registration?email=%s&amp;name=%s
                    </p>
                </body>
            </html> 

            """ % (email, name, email, name)

        text = """Welcome to Podradio, Please visit http://podradio-za.appspot.com/registration?email=%s&amp;name=%s to indicate which school/schools you are interested in listening to.""" % (email, name)

        utils.send_mandrill_confirmation_mail("Podradio Confirmation", html, text, email, 'podradiocoza@gmail.com', False)


app = webapp2.WSGIApplication([
    ('/', Home),
    ('/registration', Registration),
    ('/privacy', Privacy),

    ('/admin', Admin),
    ('/admin/add_podcast/(\w+)', AdminAddPodcast),
    ('/admin/delete_podcast', AdminDeletePodcast),
    ('/admin/add_region', AdminAddRegion),
    ('/admin/delete_region', AdminDeleteRegion),
    ('/admin/add_school/(\w+)', AdminAddSchool),
    ('/admin/delete_school', AdminDeleteSchool),
    ('/admin/in_app_message', AdminInAppMessage),
    ('/admin/emails', AdminEmails),
    ('/admin/emails/csv', AdminEmailsCSV),
    # ('/admin/refresh_data', AdminRefreshData),

    # API
    ('/api/register', APIRegister),
    ('/api/get_all_podcasts', APIGetPodcasts),
    ('/api/get_school_podcasts/(\w+)', APIGetSchoolPodcasts),
    ('/api/get_region_list', APIGetRegionList),
    ('/api/get_school_list/(\w+)', APIGetSchoolList),
    ('/api/get_message', APIGetMessage),

    ('/api/track_download', APITrackDownload),
    ('/api/track_play', APITrackPlay),


    #SEO
    ('/admin/seo', AdminSEO),

    #Settings
    ('/admin/settings', AdminSettings),

    #testing
    # ('/test_email', TestEmail)

], debug=False)

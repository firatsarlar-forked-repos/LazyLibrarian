import os, cherrypy

from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

import threading, time

import lazylibrarian

from lazylibrarian import logger, importer, database
from lazylibrarian.searchnzb import searchbook
from lazylibrarian.formatter import checked
from lazylibrarian.gr import GoodReads


def serve_template(templatename, **kwargs):

    interface_dir = os.path.join(str(lazylibrarian.PROG_DIR), 'data/interfaces/')
    template_dir = os.path.join(str(interface_dir), lazylibrarian.HTTP_LOOK)

    _hplookup = TemplateLookup(directories=[template_dir])

    try:
        template = _hplookup.get_template(templatename)
        return template.render(**kwargs)
    except:
        return exceptions.html_error_template().render()


class WebInterface(object):

    def index(self):
        raise cherrypy.HTTPRedirect("home")
    index.exposed=True

    def home(self):
        myDB = database.DBConnection()
        authors = myDB.select('SELECT * from authors order by AuthorName COLLATE NOCASE')
        return serve_template(templatename="index.html", title="Home", authors=authors)
    home.exposed = True

    def config(self):
        http_look_dir = os.path.join(lazylibrarian.PROG_DIR, 'data/interfaces/')
        http_look_list = [ name for name in os.listdir(http_look_dir) if os.path.isdir(os.path.join(http_look_dir, name)) ]

        config = {
                    "http_host":        lazylibrarian.HTTP_HOST,
                    "http_user":        lazylibrarian.HTTP_USER,
                    "http_port":        lazylibrarian.HTTP_PORT,
                    "http_pass":        lazylibrarian.HTTP_PASS,
                    "http_look":        lazylibrarian.HTTP_LOOK,
                    "http_look_list":   http_look_list,
                    "launch_browser":   checked(lazylibrarian.LAUNCH_BROWSER),
                    "logdir" :          lazylibrarian.LOGDIR,
                    "use_imp_onlyisbn": checked(lazylibrarian.IMP_ONLYISBN),
                    "imp_ignore":       lazylibrarian.IMP_IGNORE,
                    "sab_host":         lazylibrarian.SAB_HOST,
                    "sab_port":         lazylibrarian.SAB_PORT,
                    "sab_api":          lazylibrarian.SAB_API,
                    "sab_user":         lazylibrarian.SAB_USER,
                    "sab_pass":         lazylibrarian.SAB_PASS,
                    "sab_dir":          lazylibrarian.SAB_DIR,
                    "sab_cat":          lazylibrarian.SAB_CAT,
                    "usenet_retention":          lazylibrarian.USENET_RETENTION,
                    "use_blackhole":       checked(lazylibrarian.BLACKHOLE),
                    "blackholedir":        lazylibrarian.BLACKHOLEDIR,
                    "use_nzbmatrix" :   checked(lazylibrarian.NZBMATRIX),
                    "nzbmatrix_user" :  lazylibrarian.NZBMATRIX_USER,
                    "nzbmatrix_api" :   lazylibrarian.NZBMATRIX_API,
                    "use_newznab" :     checked(lazylibrarian.NEWZNAB),
                    "newznab_host" :    lazylibrarian.NEWZNAB_HOST,
                    "newznab_api" :     lazylibrarian.NEWZNAB_API,
                    "use_nzbsorg" :     checked(lazylibrarian.NZBSORG),
                    "nzbsorg_uid" :     lazylibrarian.NZBSORG_UID,
                    "nzbsorg_hash" :    lazylibrarian.NZBSORG_HASH,
                    "use_newzbin" :     checked(lazylibrarian.NEWZBIN),
                    "newzbin_uid" :     lazylibrarian.NEWZBIN_UID,
                    "newzbin_pass" :    lazylibrarian.NEWZBIN_PASS,
                }
        return serve_template(templatename="config.html", title="Settings", config=config)    
    config.exposed = True

    def configUpdate(self, http_host='0.0.0.0', http_user=None, http_port=5299, http_pass=None, http_look=None, launch_browser=0, logdir=None, imp_onlyisbn=0, imp_ignore=None,
        sab_host=None, sab_port=None, sab_api=None, sab_user=None, sab_pass=None, sab_dir=None, sab_cat=None, usenet_retention=None, blackhole=0, blackholedir=None,
        nzbmatrix=0, nzbmatrix_user=None, nzbmatrix_api=None, newznab=0, newznab_host=None, newznab_api=None, nzbsorg=0, nzbsorg_uid=None, nzbsorg_hash=None, 
        newzbin=0, newzbin_uid=None, newzbin_pass=None):

        lazylibrarian.HTTP_HOST = http_host
        lazylibrarian.HTTP_PORT = http_port
        lazylibrarian.HTTP_USER = http_user
        lazylibrarian.HTTP_PASS = http_pass
        lazylibrarian.HTTP_LOOK = http_look
        lazylibrarian.LAUNCH_BROWSER = launch_browser
        lazylibrarian.LOGDIR = logdir

        lazylibrarian.IMP_ONLYISBN = imp_onlyisbn
        lazylibrarian.IMP_IGNORE = imp_ignore

        lazylibrarian.SAB_HOST = sab_host
        lazylibrarian.SAB_PORT = sab_port
        lazylibrarian.SAB_API = sab_api
        lazylibrarian.SAB_USER = sab_user
        lazylibrarian.SAB_PASS = sab_pass
        lazylibrarian.SAB_DIR = sab_dir
        lazylibrarian.SAB_CAT = sab_cat
        lazylibrarian.USENET_RETENTION = usenet_retention
        lazylibrarian.BLACKHOLE = blackhole
        lazylibrarian.BLACKHOLEDIR = blackholedir

        lazylibrarian.NZBMATRIX = nzbmatrix
        lazylibrarian.NZBMATRIX_USER = nzbmatrix_user
        lazylibrarian.NZBMATRIX_API = nzbmatrix_api
        lazylibrarian.NEWZNAB = newznab
        lazylibrarian.NEWZNAB_HOST = newznab_host
        lazylibrarian.NEWZNAB_API = newznab_api
        lazylibrarian.NZBSORG = nzbsorg
        lazylibrarian.NZBSORG_UID = nzbsorg_uid
        lazylibrarian.NZBSORG_HASH = nzbsorg_hash
        lazylibrarian.NEWZBIN = newzbin
        lazylibrarian.NEWZBIN_UID = newzbin_uid
        lazylibrarian.NEWZBIN_PASS = newzbin_pass

        lazylibrarian.config_write()

        raise cherrypy.HTTPRedirect("config")

    configUpdate.exposed = True

#SEARCH
    def search(self, name, type):
        GR = GoodReads()
        if len(name) == 0:
            raise cherrypy.HTTPRedirect("config")
        if type == 'author':
            searchresults = GR.find_author_name(name)
        else:
            searchresults = GR.find_book_name(name)
        return serve_template(templatename="searchresults.html", title='Search Results for: "' + name + '"', searchresults=searchresults, type=type)
    search.exposed = True

#AUTHOR
    def authorPage(self, AuthorID):
        myDB = database.DBConnection()

        if lazylibrarian.IMP_ONLYISBN and lazylibrarian.IMP_IGNORE:
            language = str(lazylibrarian.IMP_IGNORE).replace(' ','')
            query = 'SELECT * from books WHERE AuthorID=%s AND NOT BookLang IN %s AND BookLang IS NOT NULL order by BookName ASC' % (AuthorID, tuple(language.split(',')) )
        elif lazylibrarian.IMP_IGNORE:
            language = str(lazylibrarian.IMP_IGNORE).replace(' ','')
            query = 'SELECT * from books WHERE AuthorID=%s AND NOT BookLang IN %s OR BookLang IS NULL order by BookName ASC' % (AuthorID, tuple(language.split(',')) )
        elif lazylibrarian.IMP_ONLYISBN:
            query = 'SELECT * from books WHERE AuthorID=%s AND BookLang IS NOT NULL order by BookName ASC' % AuthorID
        else:
            query = 'SELECT * from books WHERE AuthorID=%s order by BookName ASC' % AuthorID

        #logger.debug('DBQuery: ' + query)

        author = myDB.action('SELECT * FROM authors WHERE AuthorID=?', [AuthorID]).fetchone()
        books = myDB.select(query)
        if author is None:
            raise cherrypy.HTTPRedirect("home")
        return serve_template(templatename="author.html", title=author['AuthorName'], author=author, books=books)
    authorPage.exposed = True

    def addAuthor(self, authorid):
        threading.Thread(target=importer.addAuthorToDB, args=[authorid]).start()
        raise cherrypy.HTTPRedirect("authorPage?AuthorID=%s" % authorid)
    addAuthor.exposed = True

    def pauseAuthor(self, AuthorID):
        logger.info(u"Pausing author: " + AuthorID)
        myDB = database.DBConnection()
        controlValueDict = {'AuthorID': AuthorID}
        newValueDict = {'Status': 'Paused'}
        myDB.upsert("authors", newValueDict, controlValueDict)
        raise cherrypy.HTTPRedirect("authorPage?AuthorID=%s" % AuthorID)
    pauseAuthor.exposed = True

    def resumeAuthor(self, AuthorID):
        logger.info(u"Resuming author: " + AuthorID)
        myDB = database.DBConnection()
        controlValueDict = {'AuthorID': AuthorID}
        newValueDict = {'Status': 'Active'}
        myDB.upsert("authors", newValueDict, controlValueDict)
        raise cherrypy.HTTPRedirect("authorPage?AuthorID=%s" % AuthorID)
    resumeAuthor.exposed = True

    def deleteAuthor(self, AuthorID):
        logger.info(u"Removing author: " + AuthorID)
        myDB = database.DBConnection()
        myDB.action('DELETE from authors WHERE AuthorID=?', [AuthorID])
        myDB.action('DELETE from books WHERE AuthorID=?', [AuthorID])
        raise cherrypy.HTTPRedirect("home")
    deleteAuthor.exposed = True

    def refreshAuthor(self, AuthorID):
        importer.addAuthorToDB(ArtistID)
        raise cherrypy.HTTPRedirect("authorPage?AuthorID=%s" % AuthorID)
    refreshAuthor.exposed=True

#BOOKS
    def markBooks(self, AuthorID=None, action=None, **args):

        # update db first
        myDB = database.DBConnection()
        for bookid in args:
            # ouch dirty workaround...
            if not bookid == 'book_table_length':

                controlValueDict = {'BookID': bookid}
                newValueDict = {'Status': action}
                myDB.upsert("books", newValueDict, controlValueDict)
                logger.info('Status set to %s for BookID: %s' % (action, bookid))

        # start searchthreads
        for bookid in args:
            # ouch dirty workaround...
            if not bookid == 'book_table_length':

                if action == 'Wanted':
                    logger.info('Search started for BookID: ' + bookid)
                    searchbook(bookid)
        if AuthorID:
            raise cherrypy.HTTPRedirect("authorPage?AuthorID=%s" % AuthorID)
         ## create later, all wanted books to upcoming (or wanted.html)
#        else:
#            raise cherrypy.HTTPRedirect("upcoming")
    markBooks.exposed = True

    def logs(self):
        return serve_template(templatename="logs.html", title="Log", lineList=lazylibrarian.LOGLIST)
    logs.exposed = True

    def shutdown(self):
        lazylibrarian.config_write()
        lazylibrarian.SIGNAL = 'shutdown'
        message = 'closing ...'
        return serve_template(templatename="shutdown.html", title="Close library", message=message, timer=15)
        return page
    shutdown.exposed = True

    def restart(self):
        lazylibrarian.SIGNAL = 'restart'
        message = 'reopening ...'
        return serve_template(templatename="shutdown.html", title="Reopen library", message=message, timer=30)
    restart.exposed = True

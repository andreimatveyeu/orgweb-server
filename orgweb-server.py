#!/usr/bin/python
import cherrypy
from pyorgtree.pyorgtree import *
import sys
import os.path
import time
import cPickle

class FormatSubtree(object):
    subtree = None
    def __init__(self, subtree):
        self.subtree = subtree
        
    def get_html(self):
        out = ""
        out += '''
        <html>
        <head>
        <link rel="stylesheet" type="text/css" href="/css">
        </head>
        <body>
        <div id="wrapper">
        '''
        subtree = self.subtree
        if subtree:
            parent = subtree.get_parent()
            out += '<div id="subtree">'
            if subtree.get_header():
                out += '<h1><div id="header">%s: %s</div></h1>' % (subtree.get_header().get_hash(), subtree.get_header().get_title())
            out += '<pre>'
            out += subtree.get_data()
            out += '</pre>'
            children = subtree.get_children()
            if children:
                out += '<ul>'
                for child in children:
                    out += '<li>'
                    if child.get_header().has_hash():
                        out += '<a href="?tree_hash=%s">%s</a>' % (child.get_header().get_hash(), child.get_header().get_title())
                    else:
                        out += child.get_header().get_title()
                    out += '</li>'
                out += ''
                
            out += '</div><!-- end subtree -->'
            out += '<div id="tree_navigation">'
            if parent:
                if parent.get_header():
                    out += '<a href="?tree_hash=%s">%s</a>' % (parent.get_header().get_hash(), 
                                                               parent.get_header().get_title())
                out += "<br />"
            out += "</div> <!-- end tree_navigation -->"
        else:
            out += 'Tree not found'
        out += '<hr />'
        out += '<div id="footer">'
        out += 'orgweb-server by <a href="http://www.ideabulbs.com">Andrei Matveyeu</a>'
        out += '</div>'
        out += '</div> <!-- end wrapper -->'
        out += '</body>'
        return out

class OrgWebServer(object):
    
    orgfile = None
    cache = None
    stylecss = "styles/main.css"
    cachedir = "cache/"
    
    def __init__(self, filename):
        self.orgfile = filename
        if not os.path.exists(self.cachedir):
            try:
                os.mkdir(self.cachedir)
            except OSError:
                sys.stderr.write("Can't create cache directory!")
                sys.exit(1)
        self.cache = 'cache/' + self.orgfile.split(os.sep)[-1] + '.cache'
        if os.path.exists(self.cache):
            os.unlink(self.cache)
        
    def css(self):
        try:
            inp = open(self.stylecss, 'r')
            data = inp.read()
            inp.close()
            return data
        except IOError:
            return None
    css.exposed = True
    
    def index(self, tree_hash):
        tree = OrgTree()
        if not os.path.exists(self.cache):
            tree.read_from_file(self.orgfile, 0, 0)
            if not tree.pickle_dump(self.cache):
                print "Error dumping tree to file: %s" % self.cache
        else:
            cache_time = time.ctime(os.path.getmtime(self.cache))
            orgfile_time = time.ctime(os.path.getmtime(self.orgfile))
            if orgfile_time > cache_time:
                tree.read_from_file(self.orgfile, 0, 0)
                if not tree.pickle_dump(self.cache):
                    print "Error dumping tree to file: %s" % self.cache
            else:
                if not tree.pickle_load(self.cache):
                    print "Error loading tree from file: %s" % self.cache
                
        subtree = tree.get_tree_dict()[tree_hash]
        fs = FormatSubtree(subtree)
        result = fs.get_html()
        tree = None
        return result
        
    index.exposed = True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage: orgweb-server.py </path/to/file.org> <port_number>"
        sys.exit(1)
    cherrypy.config.update({'server.socket_host': 'localhost', 
                            'server.socket_port': int(sys.argv[2]), 
                            })
    cherrypy.quickstart(OrgWebServer(sys.argv[1]))

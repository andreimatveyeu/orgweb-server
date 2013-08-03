#!/usr/bin/python
import cherrypy
from pyorgtree.pyorgtree import *

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
                out += '<h1><div id="header">%s</div></h1>' % subtree.get_header().get_title() 
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
    def css(self):
        try:
            inp = open('styles/main.css', 'r')
            data = inp.read()
            inp.close()
            return data
        except IOError:
            return None
    css.exposed = True
    
    def index(self, tree_hash):
        tree = OrgTree()
        tree.read_from_file('/home/arilou649/org/personal.org', 0, 0)
        subtree = tree.get_tree_dict()[tree_hash]
        fs = FormatSubtree(subtree)
        return fs.get_html()
    index.exposed = True

if __name__ == "__main__":
    cherrypy.config.update({'server.socket_host': 'localhost', 
                            'server.socket_port': 8000, 
                            })
    cherrypy.quickstart(OrgWebServer())

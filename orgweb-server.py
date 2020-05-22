#!/usr/bin/env python
import cherrypy
from pyorgtree.pyorgtree import *
import sys
import os.path
import time
import pickle
import shutil

class FormatTreeBody(object):
    data = None

    def __init__(self, data):
        self.data = data

    def get_html(self):
        hash_link_pattern = re.compile(r'(?P<link>h:[a-z0-9]{5})')
        tokens = self.data.split(' ')
        result = ""
        for token in tokens:
            if hash_link_pattern.match(token):
                hash_tree = hash_link_pattern.match(token).group('link')
                if hash_tree:
                    hash_tree = hash_tree[2:]
                    token = hash_link_pattern.sub(
                        '<a href="?tree_hash=%s">%s</a>' % (hash_tree, hash_tree), token)
            result += token + " "
        return result


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
                if subtree.get_header().has_type():
                    tree_type = subtree.get_header().get_type()
                    keyword_classes = {
                        'TODO': 'todo',
                        'DONE': 'done',
                        'WAIT': 'wait'
                    }
                    if tree_type in keyword_classes:
                        style = keyword_classes[tree_type]
                    else:
                        style = "plainType"
                    out += '<h1 class="treeHeader"><span class="%s">%s</span> <span id="header">%s: %s</span></h1>' % (style, tree_type,
                                                                                                                       subtree.get_header().get_hash(),
                                                                                                                       subtree.get_header().get_title())
                else:
                    out += '<h1><div id="header">%s: %s</div></h1>' % (
                        subtree.get_header().get_hash(), subtree.get_header().get_title())
            out += '<pre>'
            ftb = FormatTreeBody(subtree.get_data())
            out += ftb.get_html()
            out += '</pre>'
            children = subtree.get_children()
            if children:
                out += '<ul>'
                for child in children:
                    out += '<li>'
                    if child.get_header().has_hash():
                        if child.get_header().has_type():
                            tree_type = child.get_header().get_type()
                            keyword_classes = {
                                'TODO': 'todo',
                                'DONE': 'done',
                                'WAIT': 'wait'
                            }
                            if tree_type in keyword_classes:
                                style = keyword_classes[tree_type]
                            else:
                                style = "plainType"
                            out += '<span class="%s">%s</span> ' % (
                                style, tree_type)
                        out += '<a href="?tree_hash=%s">%s</a>' % (
                            child.get_header().get_hash(), child.get_header().get_title())
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


class OrgCache(object):

    orgfile = None
    cache = None
    cachedir = "cache/"
    cache_time = None
    subtree = None

    def __init__(self, filename):
        self.orgfile = filename
        if os.path.exists(self.cachedir):
            shutil.rmtree(self.cachedir)

        try:
            os.mkdir(self.cachedir)
        except OSError:
            raise RuntimeError("Can't create cache directory!")

        self.cache = 'cache/' + self.orgfile.split(os.sep)[-1] + '.cache'
        if os.path.exists(self.cache):
            self.cache_time = os.path.getmtime(self.cache)
        if not self._load_subtree():
            sys.stderr.write("Can't load subtree!")
            sys.exit(1)

    def _org_file_more_uptodate(self):
        orgfile_time = os.path.getmtime(self.orgfile)
        if orgfile_time > self.cache_time:
            return True
        else:
            return False

    def _load_subtree(self):
        self.subtree = HashedOrgTree()
        if not os.path.exists(self.cache):
            self.subtree.read_from_file(self.orgfile, 0, 0)
            if not self.subtree.pickle_dump(self.cache):
                print(("Error dumping tree to file: %s" % self.cache))
                return False
            self.cache_time = os.path.getmtime(self.cache)
        else:
            if self._org_file_more_uptodate():
                print("Reloading org-file")
                self.subtree.read_from_file(self.orgfile, 0, 0)
                if not self.subtree.pickle_dump(self.cache):
                    print("Error dumping tree to file: %s" % self.cache)
                    return False
                self.cache_time = os.path.getmtime(self.cache)
            else:
                if not self.subtree.pickle_load(self.cache):
                    print("Error loading tree from file: %s" % self.cache)
                    return False
        return True


class OrgWebServer(OrgCache):

    stylecss = "styles/main.css"

    def __init__(self, filename):
        super(OrgWebServer, self).__init__(filename)

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
        if self._org_file_more_uptodate():
            if not self._load_subtree():
                sys.stderr.write("Error occured while reloading subtree")
                sys.exit(1)
        subtree = self.subtree.get_tree_dict()[tree_hash]
        fs = FormatSubtree(subtree)
        result = fs.get_html()
        return result
    index.exposed = True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: orgweb-server.py </path/to/file.org> <port_number>")
        sys.exit(1)
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 
                            'server.socket_port': int(sys.argv[2]), 
                            })

    current_dir = os.path.dirname(os.path.abspath(__file__))

    conf = {'/styles': {'tools.staticdir.on': True,
                        'tools.staticdir.dir': os.path.join(current_dir, 'styles'),
                        'tools.staticdir.content_types': {'css': 'text/css'}}}
    cherrypy.quickstart(OrgWebServer(sys.argv[1]), config=conf)

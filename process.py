#-------------------------------------------------------------------------------
# Name:  process.py
# Purpose:
#   XML conversion and routing according to specified rules in configuration
#
# Author:   Radomirs Cirskis
#
# Created:  2011-02-12
# Licence:  WTFPL
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import glob, os.path, sys, traceback
import ConfigParser
import libxml2, libxslt
from ftplib import FTP


class Rule(object):
    __slots__ = ['name','xpath','xsl','destination']
    def __init__( self, name, items):
        if isinstance(items, list):
            items = dict(items)
        self.name = name
        self.xpath = items['xpath']
        self.xsl = items['xsl']
        self.destination = items['destination']

class Destination(object):
    __slots__ = ['name','host','user','password','location']
    def __init__( self, name, items):
        if isinstance(items, list):
            items = dict(items)
        self.name = name
        self.host = items['host']
        self.user = items['user']
        self.password = items['password']
        self.location = items['location']

class XSLTransformer(object):
    """
    Object impometing XML file processing (transformin and tranfering according the configuration):
        #1 Load configuration
        #2 Poll the source dirctories (loop through the list of the source directories)
        #3 Loop through the new files
        #4 Parse file
        #5 Find transformation and routing rule arrording to the rules
        #6 Load XSLT file (if not already chached)
        #7 Parse file
        #8 Transfer file
        #9 If nothing (no file) was processed since the previous run, "sleep" for a while
    """

    config = None
    "Configuration"

    sources = []
    "List of directories to poll"
    rules = []
    "List of the rules read from the configuration"
    destinations = dict()
    "List of the destination specifications read from the configuration"
    styles = dict()
    "XSLT cache"

    def __init__(self, config_file=None):
        """
        Upon the instantiation of the object reads the configuration
        and parses it identifying all source folders, XSL selection rules,
        and destinations of transformed files.
        """
        self.config = config = ConfigParser.ConfigParser()
        try:
            if not( config_file and os.path.exists(config_file) ):
                config_file = 'XSLTransformer.cfg'
            config.read( config_file)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise Exception("Failed to read condfiguration file")
        sources = config.items('sources')
        if sources:
            self.sources = [v for (k,v) in sources]
        else:
            raise Exception("Missing source directories!")
        for sec in config.sections():
            items = config.items(sec)
            if sec.startswith('rule'):
                self.rules.append( Rule(sec, items) )
            if sec.startswith('dest'):
                self.destinations[sec] = Destination(sec, items)
        pass

    def process_file(self, file_name):
        """
        1. parses file;
        2. detects the rule to apply;
        3. parses XSL and loades into the cache (if have not yet loaded)
        4. transforms;
        5. transfers;
        """

        # TODO: check if file is not locked

        try:
            doc = libxml2.parseFile(file_name)
        except:
            # TODO: log failed file parsing
            return

        rule_to_apply = None
        for rule in self.rules:
            try:
                if doc.xpathEval( rule.xpath ):
                    rule_to_apply = rule
                    break
            except:
                # TODO: handly exeptionin XPath evaluation
                print "Unexpected error:", sys.exc_info()[0]
                pass
        if not(rule_to_apply):
            # No rule found TODO: log
            return

        if not self.styles.has_key( rule.xsl ):
            try:
                styledoc = libxml2.parseFile( rule.xsl)
                self.styles[rule.xsl] = libxslt.parseStylesheetDoc(styledoc)
            except:
                # TODO: log failed XSLT parsing
                print "Unexpected error:", sys.exc_info()[0]
                return
        style = self.styles[rule.xsl]

        try:
            file_name_main, file_name_ext = os.path.splitext(file_name)

            output_file_name = file_name_main+'_output'+file_name_ext
            result = style.applyStylesheet(doc, None)
            style.saveResultToFilename(output_file_name, result, 0)
        except:
            # TODO: log failed transformation
            print "Unexpected error:", sys.exc_info()[0]
            return
        pass

        try:
            dest = self.destinations[rule_to_apply.destination]
            ftp=FTP()
            ftp.connect( dest.host)
            ftp.login( dest.user, dest.password)
            output_file = open(output_file_name,'rb')
            ftp.storbinary('STOR %s/%s' %
                (dest.location, os.path.basename(output_file_name) ), output_file)
        except:
            # TODO: log failed transfer
            tb = traceback.format_exc()
            print "Unexpected error:", sys.exc_info()[0]
            print tb

        # TODO: move the file somewhere else and perhaps log the success

    def process_sources(self):
        for source in self.sources:
            xml_files = set(
                glob.glob( os.path.join( source, '*.xml') )
                +glob.glob( os.path.join( source, '*.XML') ))
            for f in xml_files:
                self.process_file( f)

    def start(self):
        """
        Run main loop
        """
        self.process_sources()

    def close(self):
        #TODO: cleaning
        #style.freeStylesheet()
        #doc.freeDoc()
        #result.freeDoc()
        pass

def main():
    transformer = XSLTransformer( 'XSLTransformer.cfg')
    transformer.start()

if __name__ == '__main__':
    main()

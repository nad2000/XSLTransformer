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

import glob, os.path
import ConfigParser

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

    __config = None
    "Configuration"

    __sources = []
    __rules = dict()
    __destinations = dict()
    __xsl = dict()

    def __getattr__(self, name):
        if name=='sources':
            return self.__sources
        elif name=='rules':
            return self.__rules
        elif name=='destinations':
            return self.__destinations
        elif name=='xsl' or name=='xslt':
            return self.__xsl
        else:
            raise Exception( "Undefined property")

    def __init__(self, config_file=None):
        """
        Upon the instantiation of the object reads the configuration
        and parses it identifying all source folders, XSL selection rules,
        and destinations of transformed files.
        """
        self.__config = config = ConfigParser.ConfigParser()
        try:
            if not( config_file and os.path.exists(config_file) ):
                config_file = 'XSLTransformer.cfg'
            config.read( config_file)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise Exception("Failed to read condfiguration file")
        sources = config.items('sources')
        if sources:
            self.__sources = [v for (k,v) in sources]
        else:
            raise Exception("Missing source directories!")
        for sec in config.sections():
            items = config.items(sec)
            if sec.startswith('rule'):
                self.__rules[sec] = Rule(sec, items)
            if sec.startswith('dest'):
                self.__destinations[sec] = Destination(sec, items)
        pass

    def process_file(self, file_name):
        """
        1. parses file;
        2. detects the rule to apply;
        3. parses XSL and loades into the cache (if have not yet loaded)
        4. transforms;
        5. transfers;
        """
        pass

    def process_sources(self):
        for source in self.__sources:
            xml_files = set(
                glob.glob( os.path.join( source, '*.xml') )
                +glob.glob( os.path.join( source, '*.XML') ))
            for f in xml_files:
                self.process_file( f)

    def start(self):
        self.process_sources()


def main():
    transformer = XSLTransformer( 'XSLTransformer.cfg')
    transformer.start()

if __name__ == '__main__':
    main()

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

import glob, os, os.path, sys, traceback, time, threading
import ConfigParser
import libxml2, libxslt
from ftplib import FTP
import win32evtlogutil

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

class XSLTransformer(threading.Thread):
    """
    Object implementing XML file processing (transforming and tranfering according to the configuration):
        #1 Load configuration;
        #2 Poll the source dirctories (looping through the list of the source directories);
        #3 Loop through the new files;
        #4 Parse each file;
        #5 Find transformation and routing rule;
        #6 Load XSLT file (if not already chached);
        #7 Transform the parsed source file;
        #8 Transfer file to the destination;
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

    def log_error( self, message):
        """
        Log an error message into Event Log
        """
        win32evtlogutil.ReportEvent(
            'XSLTransformer', 4, 0,
            win32evtlogutil.win32evtlog.EVENTLOG_ERROR_TYPE,
            message,
            str(traceback.print_exc(sys.exc_info()) ) )

    def process_file(self, file_name):
        """
        1. parses the source file;
        2. detects the rule to apply;
        3. parses XSL and loades into the cache (if it has not yet loaded)
        4. transforms;
        5. transfers to the destination;
        6. moves into an archive directory;
        """

        try:
            source_file = open( file_name, 'rb')
        except:
            # TODO: file might be locked, procede with the next
            return

        try:
            doc = libxml2.parseDoc( source_file.read() )
        except:
            self.log_error( "Error parsing source file %s" % file_name )
            return
        finally:
            source_file.close()

        rule_to_apply = None
        for rule in self.rules:
            try:
                if doc.xpathEval( rule.xpath ):
                    rule_to_apply = rule
                    break
            except:
                self.log_error( "Error evaluating XPath %s with file " % (rule.xpath, file_name) )
                pass
        if not(rule_to_apply):
            # self.log_error( "No rule found for %s" % file_name )
            return

        if not self.styles.has_key( rule.xsl ):
            try:
                styledoc = libxml2.parseFile( rule.xsl)
                self.styles[rule.xsl] = libxslt.parseStylesheetDoc(styledoc)
            except:
                self.log_error( "Error parsing XSL/XSLT %s" % rule.xsl )
                return
        style = self.styles[rule.xsl]

        try:
            output_dirname = os.path.join( os.path.dirname( file_name), '.output')
            if not os.path.exists(output_dirname):
                os.makedirs(output_dirname)

            file_name_basename = os.path.basename( file_name)
            output_file_name = os.path.join(
                output_dirname,
                file_name_basename[3:] if file_name_basename.startswith('IN-')
                                       else file_name_basename  )
            result = style.applyStylesheet(doc, None)
            style.saveResultToFilename(output_file_name, result, 0)
        except:
            self.log_error( "Failed to tranfrom file %s with %s" % (file_name, rule.xsl) )
            return False

        try:
            dest = self.destinations[rule_to_apply.destination]
            ftp=FTP()
            ftp.connect( dest.host)
            ftp.login( dest.user, dest.password)
            output_file = open(output_file_name,'rb')
            ftp.storbinary('STOR %s/%s' %
                (dest.location, os.path.basename(output_file_name) ), output_file)
        except:
            self.log_error( "Failed to tranfer file %s to the destination %s" %
                            (output_file_name, rule_to_apply.destination) )
            return False


        archive_name = os.path.join(
            os.path.dirname( file_name),
            '.archive',
            os.path.basename( file_name))
        try:
            # os.renames(file_name, archive_name)
            pass
        except:
            self.log_error( "Failed to archive file %s" % file_name )
            return False

        return True

    def process_sources(self):
        processed_file_count = 0
        for source in self.sources:
            xml_files = set(
                glob.glob( os.path.join( source, '*.xml') )
                +glob.glob( os.path.join( source, '*.XML') ))
            for f in xml_files:
                if self.process_file( f):
                    processed_file_count += 1
        return processed_file_count

    def run( self):
        """
        Run main loop
        """
        while True:
            self.exit_if_should()
            processed_files = self.process_sources()
            self.exit_if_should()
            if not processed_files:
                # if no files have been processed sleep for 10sec
                time.sleep( 10)

    def exit_if_should( self):
        """
        Check if received SIGNAL to stop the service
        """
        if getattr(sys,'stopservice', False):
            self.close()
            sys.exit()

    def close(self):
        #TODO: cleaning
        #style.freeStylesheet()
        #doc.freeDoc()
        #result.freeDoc()
        pass

def main():
    transformer = XSLTransformer( 'XSLTransformer.cfg')
    transformer.process_sources()

if __name__ == '__main__':
    main()

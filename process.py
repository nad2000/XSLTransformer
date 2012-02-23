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

import glob, os, os.path, sys, traceback, time, codecs
import ConfigParser
import libxml2, libxslt, unicodedata
from ftplib import FTP
import win32evtlogutil, win32evtlog


DEFALT_CONFIG_FILE = 'XSLTransformer.ini'

class MessageLevel:
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    _levelNames = {
        CRITICAL : 'CRITICAL',
        ERROR : 'ERROR',
        WARNING : 'WARNING',
        INFO : 'INFO',
        DEBUG : 'DEBUG',
        NOTSET : 'NOTSET',
        'CRITICAL' : CRITICAL,
        'ERROR' : ERROR,
        'WARN' : WARNING,
        'WARNING' : WARNING,
        'INFO' : INFO,
        'DEBUG' : DEBUG,
        'NOTSET' : NOTSET,
    }

    typemap = {
        DEBUG   : win32evtlog.EVENTLOG_INFORMATION_TYPE,
        INFO    : win32evtlog.EVENTLOG_INFORMATION_TYPE,
        WARNING : win32evtlog.EVENTLOG_WARNING_TYPE,
        ERROR   : win32evtlog.EVENTLOG_ERROR_TYPE,
        CRITICAL: win32evtlog.EVENTLOG_ERROR_TYPE,
    }

def log_message( message,
               level=MessageLevel.ERROR):
    """
    Log a message into Event Log
    """

    details = traceback.format_exc( sys.exc_info() )
    lines = (message,) if details==None else (message,details,)
    win32evtlogutil.ReportEvent(
        'XSLTransformer', 4, 0,
        MessageLevel.typemap[level],
        lines )

def log_info( message):
    log_message(
        message,
        level=MessageLevel.INFO)

def log_error( message):
    """
    Log an error message into Event Log
    """
    log_message(
        message,
        level=MessageLevel.ERROR)

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

class XSLTransformer( object):
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
                config_file = DEFALT_CONFIG_FILE
            config.read( config_file)
        except:
            log_error( "Failed to read condfiguration file %s" % config_file )
            raise Exception( "Failed to read condfiguration file %s" % config_file )

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
        try:
            self.archive_processed_files = config.getboolean('process','archive')
        except ConfigParser.NoOptionError:
            self.archive_processed_files = True
        pass

        try:
            self.debug = config.getboolean('process','debug')
        except ConfigParser.NoOptionError:
            self.debug = False
        pass

    def open(self, filename, mode='r', bufsize=-1, fallback_encoding='utf_8'):
        if "r" in mode or "a" in mode: # we are interested of detecting the mode only for read text
            try:
                f = open(filename, "rb")
                bom = bytes(f.read(4))
                f.close()
            except:
                bom=b''
            if bytes(bom[:3]) ==   b'\xEF\xBB\xBF' :
                f = codecs.open(filename, mode, "utf_8")
                f.seek(3,0)
                f.BOM = codecs.BOM_UTF8
            elif bytes(bom[:2]) == b'\xFF\xFE':
                f = codecs.open(filename, mode, "utf_16_le")
                f.seek(2,0)
                f.BOM = codecs.BOM_UTF16_LE
            elif bytes(bom[:2]) == b'\xFE\xFF':
                f = codecs.open(filename, mode, "utf_16_be")
                f.seek(2,0)
                f.BOM = codecs.BOM_UTF16_BE
            elif bytes(bom[:4]) == b'\xFF\xFE\x00\x00':
                f = codecs.open(filename, mode, "utf_32_le")
                f.seek(4,0)
                f.BOM = codecs.BOM_UTF32_LE
            elif bytes(bom[:4]) == b'\x00\x00\xFE\xFF':
                f = codecs.open(filename, mode, "utf_32_be")
                f.seek(4,0)
                f.BOM = codecs.BOM_UTF32_BE
            else:  # we assume that if there is no BOM, the encoding is UTF-8
                f = codecs.open(filename, mode, fallback_encoding)
                f.seek(0)
                f.BOM = None
            return f
        else:
            log_error( "Calling unicode.open(%s,%s,%s) that may be wrong." \
                        % (filename, mode, bufsize) )


    def process_file(self, file_name):
        """
        1. parses the source file;
        2. detects the rule to apply;
        3. parses XSL and loades into the cache (if it has not yet loaded)
        4. transforms;
        5. transfers to the destination;
        6. moves into an archive directory;
        """

        if self.debug:
            log_info( "Start processing file %s" % file_name)

        self.exit_if_stopped()
        if not os.path.exists( file_name ):
            log_error( 'File %s does not exists' % file_name)
            return False
        if not os.access( file_name, os.R_OK):
            log_error( 'No access to read file %s' % file_name)
            return False

        try:
            source_file = self.open( file_name)
        except:
            log_error( 'Failed to open file %s' % file_name )
            return False

        if self.debug:
            log_info( "File %s encodes wiht %s" % ( file_name, source_file.encoding ) )

        try:
            doc_content = source_file.read()
        except:
            log_error( 'Failed to read file %s' % file_name )
            return False

        try:
            if self.debug:
                log_info( "Parsing document:\n%s" % doc_content)

            doc = libxml2.parseDoc( doc_content)
            source_file.close()
        except:
            log_error( "Error parsing source file %s" % file_name )
            source_file.close()

            bad_file_name = os.path.join(
                os.path.dirname( file_name),
                '.bad',
                os.path.basename( file_name))

            if os.path.exists( bad_file_name):
                try:
                    os.remove( bad_file_name)
                except:
                    pass

            try:
                os.renames(file_name, bad_file_name)
                pass
            except:
                log_error( "Failed to move file %s into bad-file directory" % file_name )

            return False

        rule_to_apply = None
        for rule in self.rules:
            try:
                if doc.xpathEval( rule.xpath ):
                    rule_to_apply = rule
                    break
            except:
                log_error( "Error evaluating XPath %s with file " % (rule.xpath, file_name) )
                pass
        if not(rule_to_apply):
            log_info( "No rule found for %s" % file_name )
            return

        if not self.styles.has_key( rule.xsl ):
            try:
                styledoc = libxml2.parseFile( rule.xsl)
                self.styles[rule.xsl] = libxslt.parseStylesheetDoc(styledoc)
            except:
                log_error( "Error parsing XSL/XSLT %s" % rule.xsl )
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
            log_error( "Failed to tranfrom file %s with %s" % (file_name, rule.xsl) )
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
            log_error( "Failed to tranfer file %s to the destination %s" %
                            (output_file_name, rule_to_apply.destination) )
            return False


        if self.archive_processed_files:
            archive_name = os.path.join(
                os.path.dirname( file_name),
                '.archive',
                os.path.basename( file_name))

            if os.path.exists(archive_name):
                try:
                    os.remove( archive_name)
                except:
                    pass

            try:
                os.renames(file_name, archive_name)
            except:
                log_error( "Failed to archive file %s" % file_name )
        else:
            try:
                os.remove( file_name)
            except:
                log_error( "Error deleting the source file %s" % file_name )

        return True

    def process_sources(self):
        processed_file_count = 0
        for source in self.sources:

            if self.debug:
                log_info( "Start processing source %s" % source)

            xml_files = set(
                glob.glob( os.path.join( source, '*.xml') )
                +glob.glob( os.path.join( source, '*.XML') ))
            for f in xml_files:
                self.exit_if_stopped()
                if self.process_file( f):
                    processed_file_count += 1
        return processed_file_count

    def run( self):
        """
        Run main loop
        """
        while True:
            self.exit_if_stopped()
            processed_files = self.process_sources()
            self.exit_if_stopped()
            if not processed_files:
                # if no files have been processed sleep for 10sec
                time.sleep( 10)

    def exit_if_stopped( self):
        """
        Check if received SIGNAL to stop the service
        And exit the loop
        """
        if getattr(sys,'stopservice', False):
            self.close()
            sys.exit(0)

    def close(self):
        for style in self.styles:
            self.styles[style].freeStylesheet()
        pass

def main():
    transformer = XSLTransformer( 'XSLTransformer.ini')
    transformer.process_sources()

if __name__ == '__main__':
    main()
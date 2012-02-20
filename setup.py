#-------------------------------------------------------------------------------
# Name:  setup.py
# Purpose:
#   XML conversion and routing service setup
#
# Author:   Radomirs Cirskis
#
# Created:  2011-02-12
# Licence:  WTFPL
#-------------------------------------------------------------------------------

# Configuration settings:
NAME = 'XSLTransformerService'
DESCRIPTION = 'XSLTransformer Service'
VERSION = '1.04'
PUBLISHER = 'http://www.nowITworks.eu'
WEBSITE = PUBLISHER
REVISION = NAME + ' ' + VERSION

nsh = open('config.nsh','w')
print >>nsh, """
!define PRODUCT_NAME "%s"
!define PRODUCT_VERSION "%s"
!define PRODUCT_PUBLISHER "%s"
!define PRODUCT_WEB_SITE "%s"
!define PRODUCT_SHORT_NAME "%s"
""" % (
        DESCRIPTION,
        VERSION,
        PUBLISHER,
        WEBSITE,
        NAME )

nsh.close()

import sys
buildservice = True
if '--no-service' in sys.argv[1:]:
    buildservice = False
    sys.argv = [k for k in sys.argv if k != '--no-service']
    print sys.argv

from distutils.core import setup
import os
import py2exe
import glob
import shutil

sys.path.insert(0,os.getcwd())

def get_files(dir):
    # dig looking for files
    a= os.walk(dir)
    b = True
    filenames = []

    while (b):
        try:
            (dirpath, dirnames, files) = a.next()
            filenames.append([dirpath, tuple(files)])
        except:
            b = False
    return filenames

class Target:
    def __init__(self,**kw):
        self.__dict__.update(kw)
        self.version        = VERSION
        self.name           = NAME
        self.description    = DESCRIPTION

my_com_server_target = Target(
    description    = DESCRIPTION,
    service = ["service_module"],
    modules = ["service_module"],
    create_exe = True,
    create_dll = True)

if not buildservice:
    print 'Compiling as a Windows executable ...'
    setup(
        name = NAME ,
        description = DESCRIPTION,
        version = VERSION,
        console = [
            {
                'script':'process.py',
                'icon_resources': [(1, 'app.ico')],
                'other_resources': [(u"VERSIONTAG",1,REVISION)],
            }
        ],
        zipfile=None,
        options = {
            "py2exe":{
                'packages': 'encodings',
                'includes': 'win32com,win32service,win32serviceutil,win32event',
                "optimize": '2'
            },
        },
    )
else:
    print 'Compiling as a Windows service ...'
    setup(
        name = NAME,
        description = DESCRIPTION,
        version = VERSION,
            service = [{
                'modules':["XSLTransformerService"],
                'cmdline':'pywin32',
                'icon_resources': [(1, 'app.ico')],
                'other_resources': [(u"VERSIONTAG",1,REVISION)],
            }],
            zipfile=None,
            options = {
                'py2exe':{
                    'packages': 'encodings',
                    'includes': 'win32com,win32service,win32serviceutil,win32event,' \
                        'servicemanager,win32evtlogutil,win32evtlog',
                    'optimize': '2'
                },
            },
        )

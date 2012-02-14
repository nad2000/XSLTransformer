#-------------------------------------------------------------------------------
# Name:  XSLTransformerService.py
# Purpose:
#   XML conversion and routing service
#
# Author:   Radomirs Cirskis
#
# Created:  2011-02-12
# Licence:  WTFPL
#-------------------------------------------------------------------------------

import process
import win32serviceutil, win32event, win32service, win32evtlogutil, win32evtlog, sys, os, thread
import servicemanager
from _winreg import EnumValue, OpenKey, HKEY_LOCAL_MACHINE, KEY_ALL_ACCESS

sys.stopdriver = False

class XSLTransformerServiceLauncher(win32serviceutil.ServiceFramework):
    _svc_name_ = 'XSLTransformerService'
    _scv_display_name_ ='XSLTransformer Service'
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        sys.stopservice = True
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # Wait for terminations for max 1min
        self.main_thread.join(60)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        sys.path.insert(0,os.getcwd())
        sys.stopdriver = False
        # Find configuration:
        try:
            app_key = OpenKey(
                HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\XSLTransformerService.exe',
                0, KEY_ALL_ACCESS)
            app_key_values = dict()
            i = 0
            while True:
                value_name,value_value,value_type = EnumValue(app_key, i)
                app_key_values[value_name] = value_value
                i += 1
        except WindowsError:
            # WindowsError: [Errno 259] No more data is available
            pass
        config_file = os.path.join(
                    app_key_values['Path'] if app_key_values.has_key('Path')
                                              and os.path.exists(app_key_values['Path'])
                    else os.getcwd(),
                    'XSLTransformer.cfg' )
        win32evtlogutil.ReportEvent(
            self._svc_name_,
            4, #servicemanager.PYS_SERVICE_STARTED,
            0,  # category
            win32evtlog.EVENTLOG_ERROR_TYPE, ##win32evtlog.EVENTLOG_INFORMATION_TYPE,
            "Attempt to start service with configuration: %s" % config_file )
        self.main_thread = process.XSLTransformer(config_file)
        self.main_thread.start()
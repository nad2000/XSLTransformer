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
import win32serviceutil, win32event, win32service, sys, thread

sys.stopdriver = "false"

class XSLTransformerServiceLauncher(win32serviceutil.ServiceFramework):
    _svc_name_ = 'XSLTransformerService'
    _scv_display_name_ ='XSLTransformer Service'
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        sys.stopservice = "true"
        # Wait for terminations for max 1min
        self.main_thread.join(60)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        sys.path.insert(0,os.getcwd())
        self.main_thread = process.XSLTransformer()
        self.main_thread.start()
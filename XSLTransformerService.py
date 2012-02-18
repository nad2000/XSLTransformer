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

from process import *
import win32serviceutil, win32event, win32service, win32evtlogutil, win32evtlog, sys, os, thread
import servicemanager
from _winreg import EnumValue, OpenKey, HKEY_LOCAL_MACHINE, KEY_ALL_ACCESS

sys.stopdriver = False

class XSLTransformerServiceLauncher(win32serviceutil.ServiceFramework):

    _svc_name_ = 'XSLTransformerService'
    _svc_display_name_ = 'XSLTransformer Service'
    _svc_deps_ = ["EventLog"]

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.isAlive=True

    def SvcStop(self):
        sys.stopservice = True
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.isAlive=False


    def SvcDoRun(self):
        sys.path.insert(0,os.getcwd())
        sys.stopdriver = False

        win32evtlogutil.ReportEvent(
            self._svc_name_,servicemanager.PYS_SERVICE_STARTED,0,
            servicemanager.EVENTLOG_INFORMATION_TYPE,(self._svc_name_, ''))
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
                    DEFALT_CONFIG_FILE )
        win32evtlogutil.ReportEvent(
            self._svc_name_,
            4, #servicemanager.PYS_SERVICE_STARTED,
            0,  # category
            win32evtlog.EVENTLOG_INFORMATION_TYPE,
            ( ("Attempt to start service with configuration: %s" % config_file).encode('ascii', 'ignore'),) )
        transformer = XSLTransformer(config_file)

        self.timeout = 100
        # If no files found sleep 10 sec
        self.idle = 10000

        while self.isAlive:

            # wait for service stop signal, if timeout, loop again
            rc=win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            try:
                processed_files = transformer.process_sources()
            except:
                log_error( 'Unhandled error processing sources' )
                break

            if processed_files==0:
                # if no files have been processed sleep for 10sec
                rc=win32event.WaitForSingleObject(self.hWaitStop, self.idle)

        transformer.close()

        win32evtlogutil.ReportEvent(
            self._svc_name_,servicemanager.PYS_SERVICE_STOPPED,0,
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            ("Sevice stopped: %s" % self._svc_name_, ''))

        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

        return

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(XSLTransformerServiceLauncher)
"""
Defines a Windows service to fetch data from APIs and log activities to a database using multiprocessing.
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
from multiprocessing import Process, Event
import time
import signal
from config import SERVICE_CHECK_INTERVAL
from database import get_form_metadata, log_event
from utils import fetch_data, log_heartbeat

class DataFetcherService(win32serviceutil.ServiceFramework):
    _svc_name_ = "OS2FormsPullData"
    _svc_display_name_ = "OS2Forms Pull Forms Data Service"
    _svc_description_ = "Windows service to fetch data from OS2Forms API."

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.processes = {}
        self.stop_event = Event()

    def SvcStop(self):
        """
        Called when the service is asked to stop.
        """
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        servicemanager.LogInfoMsg("Service is stopping...")
        self.running = False
        self.stop_event.set()

        # Terminate all child processes
        for form_type, process in self.processes.items():
            if process.is_alive():
                servicemanager.LogInfoMsg(f"Terminating process for form_type: {form_type}")
                process.terminate()
                process.join()
        self.processes.clear()

        servicemanager.LogInfoMsg("Service stopped.")
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        """
        Called when the service is asked to start.
        """
        servicemanager.LogInfoMsg("Service is starting...")
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.main()

    def main(self):
        """
        Main logic of the service.
        """
        servicemanager.LogInfoMsg("Service started.")
        
        # Start heartbeat process
        heartbeat_process = Process(target=log_heartbeat, args=(self.stop_event,))
        heartbeat_process.start()
        self.processes['heartbeat'] = heartbeat_process
        servicemanager.LogInfoMsg("Heartbeat process started.")

        try:
            while self.running:
                form_metadata = get_form_metadata()  # List of dictionaries

                for metadata in form_metadata:
                    form_type = metadata.get('os2formWebformId')
                    form_source = metadata.get('source')
                    destination_system = metadata.get('destination_system')
                    sp_pull_data = metadata.get('spPullData')

                    if form_type not in self.processes or not self.processes[form_type].is_alive():
                        servicemanager.LogInfoMsg(f"Starting fetch_data process for form_type: {form_type}")
                        p = Process(
                            target=fetch_data,
                            args=(form_type, form_source, destination_system, sp_pull_data, self.stop_event)
                        )
                        p.start()
                        self.processes[form_type] = p

                time.sleep(SERVICE_CHECK_INTERVAL)

        except Exception as e:
            servicemanager.LogErrorMsg(f"Service encountered an error: {e}")
            self.SvcStop()

        finally:
            # Ensure all processes are terminated on exit
            self.SvcStop()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DataFetcherService)

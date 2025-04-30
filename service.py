"""
Defines a Windows service to fetch data from OS2Forms API.
"""

import time
from multiprocessing import Process, Event
import win32serviceutil
import win32service
import win32event
import servicemanager
from mbu_dev_shared_components.database.logging import log_heartbeat
from config import SERVICE_CHECK_INTERVAL, LOG_CONTEXT, HEARTBEAT_INTERVAL, ENV
from database import get_form_metadata
from utils import fetch_data


class DataFetcherService(win32serviceutil.ServiceFramework):
    """Windows Service to fetch data from OS2Forms API periodically."""
    _svc_name_ = "OS2FormsPullData"
    _svc_display_name_ = "OS2Forms Pull Forms Data Service"
    _svc_description_ = "Windows service to fetch data from OS2Forms API."

    def __init__(self, args):
        """
        Initialize the service with given arguments.

        Args:
            args: Command-line arguments passed to the service.
        """
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.processes = {}
        self.stop_event = Event()

    def SvcStop(self):
        """
        Handle the stop signal for the service.

        This method is invoked when the service receives a stop request.
        It stops all running processes and sets the stop event.
        """
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0xF000, ("Service is stopping...", ""))
        self.running = False
        self.stop_event.set()

        # Terminate all child processes
        for form_type, process in self.processes.items():
            if form_type == 'heartbeat':
                log_heartbeat(
                    self.stop_event.is_set(),
                    LOG_CONTEXT,
                    HEARTBEAT_INTERVAL,
                    "",
                    ENV
                )
            if process.is_alive():
                servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0xF000, (f"Terminating process for form_type: {form_type}", ""))
                process.terminate()
                process.join()
        self.processes.clear()
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0xF000, ("Service stopped.", ""))
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        """
        Handle the start signal for the service.

        This method is invoked when the service receives a start request.
        It sets the service status to running and calls the main logic.
        """
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0xF000, ("Service is starting...", ""))
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        except Exception as e:
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0xF000, (f"Service encountered an error: {e}", ""))
            print(e)
        self.main()

    def main(self):
        """
        Main logic of the service.

        This method initializes the heartbeat process and periodically
        fetches metadata to start data-fetching processes for each form type.
        """
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0xF000, ("Service started.", ""))

        # Start heartbeat process
        heartbeat_process = Process(target=log_heartbeat, args=(
            self.stop_event.is_set(),
            LOG_CONTEXT,
            HEARTBEAT_INTERVAL,
            "",
            ENV))
        heartbeat_process.start()
        self.processes['heartbeat'] = heartbeat_process
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0xF000, ("Heartbeat process started.", ""))

        try:
            while self.running:
                form_metadata = get_form_metadata()  # List of dictionaries

                for metadata in form_metadata:
                    form_type = metadata.get('os2formWebformId')
                    form_source = metadata.get('source')
                    destination_system = metadata.get('destination_system')
                    sp_pull_data = metadata.get('spPullData')

                    if form_type not in self.processes or not self.processes[form_type].is_alive():
                        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0xF000, (f"Starting fetch_data process for form_type: {form_type}", ""))
                        p = Process(
                            target=fetch_data,
                            args=(form_type, form_source, destination_system, sp_pull_data, self.stop_event)
                        )
                        p.start()
                        self.processes[form_type] = p

                time.sleep(SERVICE_CHECK_INTERVAL)

        except Exception as e:
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0xF000, (f"Service encountered an error: {e}", ""))
            self.SvcStop()

        finally:
            # Ensure all processes are terminated on exit
            self.SvcStop()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DataFetcherService)

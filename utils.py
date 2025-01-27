"""
Utility functions for API calls and logging a heartbeat.
"""

import os
import json
import time
from mbu_dev_shared_components.os2forms import forms
from config import BASE_API_URL, FETCH_INTERVAL, HEARTBEAT_INTERVAL
from database import log_event, execute_stored_procedure


def fetch_data(form_type, form_source, destination_system, sp_pull_data, stop_event):
    """
    Fetch data from the API for a given form type and log results to a database.

    Args:
        form_type (str): The form type to fetch data for.
        form_source (str): Source identifier for the form.
        destination_system (str): Destination system identifier.
        sp_pull_data (str): Stored procedure name for pulling data.
        stop_event (multiprocessing.Event): Event to signal process termination.
    """
    while not stop_event.is_set():
        try:
            connection_string = os.getenv('DbConnectionString')
            api_key = os.getenv('Os2ApiKey')

            response = forms.get_list_of_active_forms(BASE_API_URL, form_type, api_key)
            forms_dict = response.json().get('submissions', {})

            log_event(f"Fetching data from: {form_type}", "INFO")
            if response.status_code == 200:
                for form in forms_dict:
                    form_url = forms_dict[form]
                    forms_response = forms.get_form(form_url, api_key)
                    form_sid = forms_response.json()['entity']['sid'][0]['value']
                    form_id = forms_response.json()['entity']['uuid'][0]['value']
                    form_type_fetched = forms_response.json()['entity']['webform_id'][0]['target_id']
                    form_submitted_date = forms_response.json()['entity']['completed'][0]['value']
                    form_data = json.dumps(forms_response.json(), ensure_ascii=False)
                    sql_params = {
                        "form_id": ("str", f'{form_id}'),
                        "form_sid": ("str", f'{form_sid}'),
                        "form_type": ("str", f'{form_type_fetched}'),
                        "form_source": ("str", f'{form_source}'),
                        "form_data": ("str", f'{form_data}'),
                        "form_submitted_date": ("str", f'{form_submitted_date}'),
                        "destination_system": ("str", f'{destination_system}'),
                    }
                    execute_stored_procedure(connection_string, sp_pull_data, sql_params)
            else:
                log_event(f"Error fetching data for {form_type}: {response.status_code}", "ERROR")

        except Exception as e:
            log_event(f"Error fetching data for {form_type}: {e}", "ERROR")

        log_event(f"Fetching data ended for {form_type}", "INFO")
        time.sleep(FETCH_INTERVAL)


def log_heartbeat(stop_event):
    """
    Logs a heartbeat to indicate the service is running.

    Args:
        stop_event (multiprocessing.Event): Event to signal process termination.
    """
    while not stop_event.is_set():
        log_event("Service is running.", "INFO")
        time.sleep(HEARTBEAT_INTERVAL)

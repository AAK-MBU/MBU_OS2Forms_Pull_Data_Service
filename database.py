"""
Handles database connections, queries, and logging events using SQL Server.
"""

import os
from typing import Dict, Any, Union
import pyodbc


def get_connection():
    """
    Establish a connection to the SQL Server database.

    Returns:
        pyodbc.Connection: A connection object for the database.
    """
    connection_string = os.getenv('DbConnectionString')
    return pyodbc.connect(connection_string)


def get_form_metadata():
    """
    Fetches form types and related information from the database.

    Returns:
        list: A list of dictionaries containing form type details.
    """
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Define the SQL query with the additional columns
        query = """
            SELECT
                [os2formWebformId],
                [source],
                [destination_system],
                [spPullData]
            FROM
                [RPA].[journalizing].[Metadata]
        """

        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        form_metadata = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return form_metadata

    except Exception as e:
        log_event(f"Error fetching form metadata: {e}", "ERROR")
        return []

    finally:
        cursor.close()
        connection.close()


def execute_stored_procedure(connection_string: str, stored_procedure: str, params: Dict[str, Any]) -> Dict[str, Union[bool, str, Any]]:
    """
    Executes a stored procedure with the given parameters.

    Args:
        connection_string (str): The connection string to connect to the database.
        stored_procedure (str): The name of the stored procedure to execute.
        params (Dict[str, Any]): A dictionary of parameters to pass to the stored procedure.
                                 Each value should be a tuple of (type, actual_value).

    Returns:
        Dict[str, Union[bool, str, Any]]: A dictionary containing the output message and error message.
    """
    result = {
        "message": None,         # For the output parameter @ResultMessage
        "error_message": None,   # For any errors encountered
    }

    try:
        with pyodbc.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                # Separate input parameters from output parameters
                input_params = {k: v for k, v in params.items() if not k.lower().startswith('@resultmessage')}

                # Prepare SQL statement
                # Declare the output variable
                sql = "DECLARE @ResultMessage NVARCHAR(500); "

                # Add EXEC statement with input parameters and output parameter
                # Build parameter assignments for EXEC
                exec_params = []
                exec_param_assignments = []
                for key in input_params:
                    exec_param_assignments.append(f"@{key} = ?")
                    exec_params.append(input_params[key][1])  # Only the actual_value

                # Append the output parameter assignment
                exec_param_assignments.append("@ResultMessage = @ResultMessage OUTPUT")

                # Combine all parameter assignments
                exec_params_str = ", ".join(exec_param_assignments)
                sql += f"EXEC {stored_procedure} {exec_params_str}; "

                # Select the output parameter
                sql += "SELECT @ResultMessage AS ResultMessage;"

                # Execute the SQL with input parameters
                cursor.execute(sql, exec_params)

                conn.commit()
    except pyodbc.DatabaseError as e:
        result["error_message"] = f"Database error: {str(e)}"
        log_event(f"Database error: {str(e)}", "ERROR")
    except ValueError as e:
        result["error_message"] = f"Value error: {str(e)}"
        log_event(f"Value error: {str(e)}", "ERROR")
    except Exception as e:
        result["error_message"] = f"An unexpected error occurred: {str(e)}"
        log_event(f"An unexpected error occurred: {str(e)}", "ERROR")

    return result


def log_event(message, level):
    """
    Logs an event to the database.

    Args:
        message (str): The log message.
        level (str): The log level (e.g., "INFO", "ERROR").
    """
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO journalizing.Service_Log (level, message, created_at)
            VALUES (?, ?, GETDATE())
            """,
            (level, message)
        )
        connection.commit()
    except Exception as e:
        print(f"Error logging event: {e}")
    finally:
        cursor.close()
        connection.close()

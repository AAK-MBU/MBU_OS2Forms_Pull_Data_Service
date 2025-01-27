# MBU OS2Forms Pull Data Service

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Windows](https://img.shields.io/badge/Platform-Windows-blue)

## Overview

`MBU_OS2Forms_Pull_Data_Service` is a Windows service designed to fetch data from the OS2Forms API. It enables automated data retrieval and processing from various forms to streamline workflows and integrate with destination systems.

## Features

- Runs as a Windows service.
- Periodically fetches metadata from OS2Forms.
- Spawns child processes to handle data retrieval per form type.
- Heartbeat logging to monitor service health.

## Prerequisites

1. **Python**: Version 3.8 or higher.
2. **Windows OS**: This service is designed specifically for Windows.
3. **Dependencies**: Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/AAK-MBU/MBU_OS2Forms_Pull_Data_Service.git
    cd MBU_OS2Forms_Pull_Data_Service
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Configure the service:
   - Update `config.py` with your application-specific settings

4. Install the service:
    ```bash
    python service.py install
    ```

## Usage

- **Starting the Service**:
  Use the following command to start the service:
  ```bash
  python service.py start

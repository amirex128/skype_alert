# README.md

## Project Overview

This project is a Python application that interacts with Skype and sends alerts based on certain events. It uses the `skpy` library to interact with Skype, `pygame` for sound, `kavenegar` for sending SMS, and `pystray` for system tray icon functionality.

## Setup

Before running the application, you need to set up your credentials and configuration:

1. Create a new file named `credentials.txt` based on the `credentials.txt.sample` file. Fill in your Skype username and password, Kavenegar API key, and sender number.

2. Modify the `config.json` file to suit your needs. This file contains the following fields:
    - `my_name`: Your name.
    - `massoud_user`: The username of the Massoud user.
    - `devops_user`: The username of the DevOps user.
    - `sobala_user`: The username of the Sobala user.
    - `call_name_list`: A list of call names.
    - `my_phone`: Your phone number.
    - `sms_alert`: A boolean value indicating whether to send SMS alerts.

## Running the Application

To run the application, use the following command:

```bash
python ./main.py
```
or
```bash
python3 ./main.py
```

## Building an Executabl

To build an executable file from this project, use the following command:

```bash
pyinstaller main.spec
```
And then run the executable file from the `dist` directory.
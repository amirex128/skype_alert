# README.md

## Project Overview

This project is a Python application that interacts with Skype and sends alerts based on certain events. It uses the `skpy` library to interact with Skype, `pygame` for sound, `kavenegar` for sending SMS, and `pystray` for system tray icon functionality.

## Installation
Install Package Requirements:
```bash
pip install -r requirements.txt
```

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
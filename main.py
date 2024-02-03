import datetime
from skpy import Skype, SkypeAuthException, SkypeEventLoop, SkypeMessageEvent, SkypeCallEvent
import pygame
import ctypes
from kavenegar import *
import platform
import pystray
from PIL import Image
import threading
import logging
import sys
import os
from art import *
import json
import tkinter as tk
from tkinter import simpledialog, messagebox

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)
kavenegar_api = KavenegarAPI('')
kavenegarParams = {}
sms_alert = False

my_name = ''
users_must_be_in_call = {}
devops_user = ''
sobala_user = ''
contacts = {}

call_name_list = []

last_show_message_time = datetime.datetime.now() - datetime.timedelta(seconds=240)
last_show_private_message_time = datetime.datetime.now() - datetime.timedelta(seconds=240)

is_stop = False


class MySkype(SkypeEventLoop):
    def __init__(self, *args, **kwargs):
        super(MySkype, self).__init__(*args, **kwargs)
        print(text2art("Skype Alert"))

    def onEvent(self, event):
        if is_stop:
            sys.exit()

        try:
            if isinstance(event, SkypeCallEvent):
                if event.msg.userId == devops_user:
                    self.show_message('گروه دو آپس کال شده است')

            if isinstance(event, SkypeCallEvent):
                if event.msg.userId == sobala_user:
                    self.show_message('گروه سوبالا کال شده است')

            if isinstance(event, SkypeMessageEvent):
                if hasattr(event.msg, 'plain'):
                    if my_name in event.msg.plain:
                        self.show_message('شما صدا زده شده اید')

                    for name, user_id in users_must_be_in_call.items():
                        if event.msg.userId == user_id:
                            self.show_message(f'{name} پیام داده است', private=True, sound=False)

                    if event.msg.userId == devops_user:
                        if '@Masood' in event.msg.plain:
                            self.show_message('مسعود داخل گروه دو آپس صدا زده شده است')
                        if check_string_existence(event.msg.plain, call_name_list):
                            self.show_message('در مورد شما در گروه دو آپس صحبت شده است', sound=False)

                    if event.msg.userId == sobala_user:
                        if check_string_existence(event.msg.plain, call_name_list):
                            self.show_message('در مورد شما در گروه سوبالا صحبت شده است', sound=False)

        except Exception as e:
            logging.error("Exception occurred on event", exc_info=True)

    def show_message(self, message, *args, **kwargs):
        sound = kwargs.get('sound', True)
        private = kwargs.get('sound', False)
        if private:
            global last_show_private_message_time
            if (datetime.datetime.now() - last_show_private_message_time).total_seconds() < 240:
                return
            last_show_private_message_time = datetime.datetime.now()
        else:
            global last_show_message_time
            if (datetime.datetime.now() - last_show_message_time).total_seconds() < 20:
                return
            last_show_message_time = datetime.datetime.now()

        if platform.system() == 'Linux' and sound and sms_alert:
            kavenegar_api.sms_send(kavenegarParams)
        else:
            if sound:
                pygame.mixer.music.play()
            ctypes.windll.user32.MessageBoxW(0, message, "SnappFood Alert", 1)
            if sound:
                pygame.mixer.music.stop()


def check_string_existence(target_string, string_list):
    return any(s in target_string for s in string_list)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def start():
    try:
        credentials_path = resource_path('credentials.txt')
        token_path = resource_path('token.txt')
        snapp_path = resource_path('snapp.mp3')
        logo_path = resource_path('logo.png')
        config_path = resource_path('config.json')

        global kavenegar_api
        with open(credentials_path, 'r') as f:
            username = f.readline().strip()
            password = f.readline().strip()
            kavenegar_api = KavenegarAPI(f.readline().strip())
            sender = f.readline().strip()

        sk = Skype(connect=False)
        sk.conn.setTokenFile(token_path)
        try:
            sk.conn.readToken()
        except SkypeAuthException:
            sk.conn.setUserPwd(username, password)
            sk.conn.getSkypeToken()

        skEvent = MySkype(tokenFile=token_path, autoAck=True)

        sk.contacts.skype.contacts.sync()
        contacts_sync = sk.contacts.skype.contacts.cache

        for value in contacts_sync.items():
            try:
                contacts[value[1].name.first + ' ' + value[1].name.last] = value[0]
            except:
                pass

        with open('config.json', 'r') as file:
            config = json.load(file)

        # List of keys to check and update
        keys = ['my_name', 'my_phone', 'sms_alert', 'call_name_list']

        # Create a tkinter root widget
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        rewrite = messagebox.askyesno(title="Configuration", message="Do you want to rewrite the config.json file?")

        # Iterate over the keys
        for key in keys:
            # If the user wants to rewrite the file or the key's value is empty
            if rewrite or not config[key]:
                # Special case for call_name_list
                if key == 'call_name_list':
                    # Ask the user for a comma-separated list of names
                    user_input = simpledialog.askstring(title="Configuration",
                                                        prompt="Enter a list of names, separated by commas:")

                    # If the user provided input, split it on commas and strip whitespace to get a list of names
                    if user_input:
                        config[key] = [name.strip() for name in user_input.split(',')]
                else:
                    # Ask the user for input
                    user_input = simpledialog.askstring(title="Configuration", prompt=f"Enter {key}:")

                    # If the user provided input, update the config
                    if user_input:
                        config[key] = user_input
                        # Create a new top-level window

        top = tk.Toplevel(root)
        # Create a Listbox widget with MULTIPLE selection mode
        listbox = tk.Listbox(top, selectmode=tk.MULTIPLE)
        # Populate the Listbox with the names of the contacts
        for name in contacts.keys():
            listbox.insert(tk.END, name)
        listbox.pack()

        # Function to handle button click
        def on_button_click():
            # Get the selected contacts
            selected_contacts = listbox.curselection()
            config['users_must_be_in_call'] = {}
            # Find their corresponding IDs and save them to users_must_be_in_call
            for i in selected_contacts:
                name = listbox.get(i)
                user_id = contacts[name]
                config['users_must_be_in_call'].update({name: user_id})

            with open('config.json', 'w') as file:
                json.dump(config, file, indent=4)
            root.destroy()
            start_skype(config, logo_path, sender, skEvent, snapp_path)

        # Create a button that saves the selected contacts when clicked
        button = tk.Button(top, text="Save", command=on_button_click)
        button.pack()

        root.mainloop()


    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        start()


def start_skype(config, logo_path, sender, skEvent, snapp_path):
    global my_name, devops_user, sobala_user, call_name_list, kavenegarParams, sms_alert, users_must_be_in_call
    my_name = config['my_name']
    my_phone = config['my_phone']
    devops_user = config['devops_user']
    sobala_user = config['sobala_user']
    call_name_list = config['call_name_list']
    users_must_be_in_call = config['users_must_be_in_call']
    sms_alert = config['sms_alert'] == 'true'
    kavenegarParams = {
        'receptor': my_phone,
        'message': 'از اسنپ فود پیام دارید',
        'sender': sender
    }
    pygame.mixer.init()
    pygame.mixer.music.load(snapp_path)
    image = Image.open(logo_path)
    menu = (pystray.MenuItem('Exit', lambda icon, item: exit_action(icon, item, skEvent)),)
    icon = pystray.Icon("name", image, "My System Tray Icon", menu)
    threading.Thread(target=skEvent.loop).start()
    icon.run(setup)


def exit_action(icon, item, skEvent):
    icon.stop()
    global is_stop
    is_stop = True
    skEvent.onEvent(SkypeCallEvent())
    sys.exit()


def setup(icon):
    icon.visible = True


if __name__ == '__main__':
    start()

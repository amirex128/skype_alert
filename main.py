import datetime
from skpy import Skype, SkypeAuthException, SkypeEventLoop, SkypeMessageEvent, SkypeCallEvent
import pygame
import ctypes
from kavenegar import *
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
import random

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)
my_name = ''
users_must_be_in_call = {}
devops_user = ''
sobala_user = ''
contacts = {}

kavenegar_api = KavenegarAPI('')
sender = ''

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
                if event.msg.userId in devops_user:
                    self.show_message('گروه دو آپس کال شده است')

            if isinstance(event, SkypeCallEvent):
                if event.msg.userId in sobala_user:
                    self.show_message('گروه سوبالا کال شده است')

            if isinstance(event, SkypeMessageEvent):
                if hasattr(event.msg, 'plain'):
                    if my_name in event.msg.plain:
                        self.show_message('شما صدا زده شده اید')

                    for name, user_id in users_must_be_in_call.items():
                        if event.msg.userId in user_id:
                            self.show_message(f'{name} پیام داده است', private=True, sound=False)

                    if event.msg.userId in devops_user:
                        if '@Masood' in event.msg.plain:
                            self.show_message('مسعود داخل گروه دو آپس صدا زده شده است')
                        if check_string_existence(event.msg.plain, call_name_list):
                            self.show_message('در مورد شما در گروه دو آپس صحبت شده است', sound=False)

                    if event.msg.userId in sobala_user:
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

        global kavenegar_api, sender
        with open(credentials_path, 'r') as f:
            kavenegar_api = KavenegarAPI(f.readline().strip())
            sender = f.readline().strip()

        sk = Skype(connect=False)
        sk.conn.setTokenFile(token_path)
        try:
            sk.conn.readToken()
        except SkypeAuthException:
            root = tk.Tk()
            root.withdraw()
            username = simpledialog.askstring(title="Authentication", prompt="Enter your Skype username:")
            password = simpledialog.askstring(title="Authentication", prompt="Enter your Skype password:", show='*')
            sk.conn.setUserPwd(username, password)
            sk.conn.getSkypeToken()
            root.destroy()

        skEvent = MySkype(tokenFile=token_path, autoAck=True)

        sk.contacts.skype.contacts.sync()
        contacts_sync = sk.contacts.skype.contacts.cache

        # Initialize the sorted_contacts dictionary
        sorted_contacts = {}

        # Loop over the contacts
        for value in contacts_sync.items():
            try:
                # Generate a key
                key = value[1].name.first + ' ' + value[1].name.last

                # Check if the key already exists in the dictionary
                while key in sorted_contacts:
                    # If the key exists, append a random integer to the end of the key
                    key += ' ' + str(random.randint(1, 100))

                # Add the entry to the dictionary
                sorted_contacts[key] = value[1].id
            except:
                pass

        # Sort the keys of the dictionary
        sorted_keys = sorted(sorted_contacts.keys())

        # Create a new dictionary with sorted keys
        contacts = {key: sorted_contacts[key] for key in sorted_keys}

        config_path = resource_path('config.json')

        with open(config_path, 'r') as file:
            config = json.load(file)

        config['my_name'] = '@' + sk.skype.user.name.first + ' ' + sk.skype.user.name.last
        keys = ['call_name_list']

        root = tk.Tk()
        root.withdraw()
        rewrite = messagebox.askyesno(title="Configuration", message="Do you want to rewrite the config.json file?")

        for key in keys:
            if rewrite or not config[key]:
                if key == 'call_name_list':
                    user_input = simpledialog.askstring(title="Configuration",
                                                        prompt="Enter a list of names, separated by commas:")

                    if user_input:
                        config[key] = [name.strip() for name in user_input.split(',')]
                else:
                    user_input = simpledialog.askstring(title="Configuration", prompt=f"Enter {key}:")

                    if user_input:
                        config[key] = user_input

        if rewrite or not config['users_must_be_in_call']:
            top = tk.Toplevel(root)
            listbox = tk.Listbox(top, selectmode=tk.MULTIPLE)
            for name in contacts.keys():
                listbox.insert(tk.END, name)
            listbox.pack()

            def on_button_click():
                selected_contacts = listbox.curselection()
                config['users_must_be_in_call'] = {}
                for i in selected_contacts:
                    name = listbox.get(i)
                    user_id = contacts[name]
                    config['users_must_be_in_call'].update({name: user_id})

                root.destroy()
                start_skype(config, skEvent)

            button = tk.Button(top, text="Save", command=on_button_click)
            button.pack()
            root.mainloop()

        start_skype(config, skEvent)


    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        start()


def start_skype(config, skEvent):
    config_path = resource_path('config.json')
    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    global my_name, devops_user, sobala_user, call_name_list, users_must_be_in_call
    my_name = config['my_name']
    devops_user = config['devops_user']
    sobala_user = config['sobala_user']
    call_name_list = config['call_name_list']
    users_must_be_in_call = config['users_must_be_in_call']

    pygame.mixer.init()
    snapp_path = resource_path('snapp.mp3')
    pygame.mixer.music.load(snapp_path)
    logo_path = resource_path('logo.png')
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

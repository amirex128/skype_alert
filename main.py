import datetime
from skpy import Skype, SkypeAuthException, SkypeGroupChat, SkypeEventLoop, SkypeMessageEvent, SkypeCallEvent
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
import time

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)
my_name = ''
users_must_be_in_call = {}
groups_must_be_in_call = {}
devops_user = ''
contacts = {}
groups = {}

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
        self.connection_checker = threading.Thread(target=self.check_connection)
        self.connection_checker.start()
        self.stop_event = threading.Event()
        self.skype_thread = None

    def start_skype_thread(self):
        try:
            print('Skype thread started')
            while not self.stop_event.is_set():
                self.loop()
        except Exception as e:
            logging.error("Exception occurred", exc_info=True)
            self.skype_thread = None

    def check_connection(self):
        before_disconnected = False
        while True:
            print("Checking connection...")
            try:
                response = requests.get('https://www.skype.com')
                response.raise_for_status()
                print("Connection is okay.")
                if before_disconnected:
                    before_disconnected = False
                    print("Connection is okay after reconnect.")
                    if self.skype_thread is not None:
                        self.stop_event.set()
                    self.stop_event = threading.Event()
                    self.skype_thread = threading.Thread(target=self.start_skype_thread)
                    self.skype_thread.start()
            except (requests.ConnectionError, requests.HTTPError):
                before_disconnected = True
                print("Connection lost. Reconnecting...")
                self.conn.readToken()
                if self.conn.connected:
                    try:
                        response = requests.get('https://www.skype.com')
                        response.raise_for_status()
                        print("Connection is okay after reconnect.")
                    except (requests.ConnectionError, requests.HTTPError):
                        print("Reconnection failed.")
                        time.sleep(10)
                        self.skype_thread = None
                        continue
                    print("Reconnected. Restarting event loop...")
                    if self.skype_thread is not None:
                        self.stop_event.set()
                    self.stop_event = threading.Event()
                    self.skype_thread = threading.Thread(target=self.start_skype_thread)
                    self.skype_thread.start()
                else:
                    print("Reconnection failed.")
            time.sleep(30)

    def onEvent(self, event):
        if is_stop:
            print('Skype event loop stopped')
            os._exit(0)
            return

        try:
            if isinstance(event, SkypeCallEvent):
                for name, user_id in groups_must_be_in_call.items():
                    if user_id == event.msg.chatId:
                        self.show_message(f'{name}این گروه کال شده است ')

            if isinstance(event, SkypeMessageEvent):
                if hasattr(event.msg, 'plain'):
                    if my_name in event.msg.plain:
                        self.show_message('شما صدا زده شده اید')

                    for name, user_id in users_must_be_in_call.items():
                        if user_id in event.msg.chatId:
                            self.show_message(f'{name} پیام داده است', private=True, sound=False)

                    for name, user_id in groups_must_be_in_call.items():
                        if user_id == event.msg.chatId:
                            if check_string_existence(event.msg.plain, call_name_list):
                                self.show_message(f'{name}در مورد شما در این گروه صحبت شده است', sound=False)

                    if devops_user == event.msg.chatId:
                        if '@Masood' in event.msg.plain:
                            self.show_message('مسعود داخل گروه دو آپس صدا زده شده است')


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
        ctypes.windll.user32.MessageBoxW(0, message, "SnappFood Alert", 1 | 16)
        print('send message: ' + message)
        if sound:
            pygame.mixer.music.stop()


def start():
    try:
        sk, sk_event = connect_skype()

        get_contacts(sk)
        get_groups(sk)

        config = set_username(sk)

        rewrite = show_config_input(config)

        show_contacts_window(config, rewrite)

        show_groups_window(config, rewrite)

        start_skype(config, sk_event)


    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        start()


def set_username(sk):
    config_path = resource_path('config.json')
    with open(config_path, 'r') as file:
        config = json.load(file)
    config['my_name'] = '@' + sk.skype.user.name.first + ' ' + sk.skype.user.name.last
    print('set my name: ' + config['my_name'])
    return config


def show_config_input(config):
    keys = ['call_name_list']
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
    print('Configs input is set')
    return rewrite


def show_contacts_window(config, rewrite):
    if rewrite or not config['users_must_be_in_call']:
        root = tk.Tk()
        root.withdraw()
        top = tk.Toplevel(root)
        listbox = tk.Listbox(top, selectmode=tk.MULTIPLE)
        for name in contacts.keys():
            listbox.insert(tk.END, name)
        listbox.pack()

        def on_button_contacts_click():
            selected_contacts = listbox.curselection()
            config['users_must_be_in_call'] = {}
            for i in selected_contacts:
                name = listbox.get(i)
                user_id = contacts[name]
                config['users_must_be_in_call'].update({name: user_id})
            top.destroy()
            root.destroy()
            print('Contacts selected')

        button = tk.Button(top, text="Save", command=on_button_contacts_click)
        button.pack()
        root.mainloop()


def show_groups_window(config, rewrite):
    if rewrite or not config['groups_must_be_in_call']:
        root = tk.Tk()
        root.withdraw()
        top = tk.Toplevel(root)
        listbox = tk.Listbox(top, selectmode=tk.MULTIPLE)
        for name in groups.keys():
            listbox.insert(tk.END, name)
        listbox.pack()

        def on_button_groups_click():
            selected_groups = listbox.curselection()
            config['groups_must_be_in_call'] = {}
            for i in selected_groups:
                name = listbox.get(i)
                user_id = groups[name]
                config['groups_must_be_in_call'].update({name: user_id})

            top.destroy()
            root.destroy()
            print('Groups selected')

        button = tk.Button(top, text="Save", command=on_button_groups_click)
        button.pack()
        root.mainloop()


def connect_skype():
    credentials_path = resource_path('credentials.txt')
    token_path = resource_path('token.txt')
    global kavenegar_api, sender
    with open(credentials_path, 'r') as f:
        kavenegar_api = KavenegarAPI(f.readline().strip())
        sender = f.readline().strip()
    sk = Skype(connect=False)
    sk.conn.setTokenFile(token_path)
    try:
        relogin = messagebox.askyesno(title="Re-Login", message="Do you want to re-login?")
        if relogin:
            raise SkypeAuthException
        sk.conn.readToken()
    except SkypeAuthException:
        root = tk.Tk()
        root.withdraw()
        username = simpledialog.askstring(title="Authentication", prompt="Enter your Skype username:")
        password = simpledialog.askstring(title="Authentication", prompt="Enter your Skype password:", show='*')
        print('Connecting to Skype...')
        sk.conn.setUserPwd(username, password)
        sk.conn.getSkypeToken()
        root.destroy()
    print('Skype connected')
    sk_event = MySkype(tokenFile=token_path, autoAck=True)
    return sk, sk_event


def get_contacts(sk):
    global contacts
    sk.contacts.skype.contacts.sync()
    contacts_sync = sk.contacts.skype.contacts.cache
    sorted_contacts = {}
    for value in contacts_sync.items():
        try:
            key = value[1].name.first + ' ' + value[1].name.last
            while key in sorted_contacts:
                key += ' ' + str(random.randint(1, 100))
            sorted_contacts[key] = value[1].id
        except:
            pass
    sorted_keys = sorted(sorted_contacts.keys())
    contacts = {key: sorted_contacts[key] for key in sorted_keys}
    print('Contacts synced')


def get_groups(sk):
    global groups
    groups_sync = sk.chats.recent()
    groups = {}
    for value in groups_sync.items():
        if isinstance(value[1], SkypeGroupChat):
            key = value[1].topic
            groups[key] = value[1].id
    print('Groups synced')


def start_skype(config, sk_event):
    try:
        set_configs(config)
        icon = register_tray(sk_event)
        threading.Thread(target=start_skype_thread, args=(sk_event,)).start()
        icon.run(setup_icon)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        start_skype(config, sk_event)


def register_tray(sk_event):
    pygame.mixer.init()
    snapp_path = resource_path('snapp.mp3')
    pygame.mixer.music.load(snapp_path)
    logo_path = resource_path('logo.png')
    image = Image.open(logo_path)
    menu = (pystray.MenuItem('Exit', lambda icon, item: exit_action(icon, item, sk_event)),)
    icon = pystray.Icon("name", image, "My System Tray Icon", menu)
    return icon


def set_configs(config):
    config_path = resource_path('config.json')
    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    global my_name, devops_user, call_name_list, users_must_be_in_call, groups_must_be_in_call
    my_name = config['my_name']
    devops_user = config['devops_user']
    call_name_list = config['call_name_list']
    users_must_be_in_call = config['users_must_be_in_call']
    groups_must_be_in_call = config['groups_must_be_in_call']

    print('word that must be in call:')
    for word in call_name_list:
        print('- ' + word)

    print('user that must be in call:')
    for name, user_id in users_must_be_in_call.items():
        print(f'- {name}: {user_id}')

    print('groups that must be in call:')
    for name, user_id in groups_must_be_in_call.items():
        print(f'- {name}: {user_id}')

    print('Configs set')


def start_skype_thread(sk_event):
    try:
        print('Skype thread started')
        sk_event.loop()
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        start_skype_thread(sk_event)


def exit_action(icon, item, sk_event):
    global is_stop
    is_stop = True
    sk_event.onEvent(SkypeCallEvent())
    print('Exit application')
    icon.stop()
    os._exit(0)


def setup_icon(icon):
    icon.visible = True


def check_string_existence(target_string, string_list):
    return any(s in target_string for s in string_list)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    start()

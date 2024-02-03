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

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)
kavenegar_api = KavenegarAPI('')
kavenegarParams = {}
sms_alert = False

my_name = ''
massoud_user = ''
devops_user = ''
sobala_user = ''

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

            if isinstance(event, SkypeMessageEvent):
                if hasattr(event.msg, 'plain'):
                    if my_name in event.msg.plain:
                        self.show_message('شما صدا زده شده اید')

                    if event.msg.userId == massoud_user:
                        self.show_message('مسعود پیام داده است', private=True)

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
        with open(config_path, 'r') as f:
            config = json.load(f)

        global my_name, massoud_user, devops_user, sobala_user, call_name_list, kavenegarParams,sms_alert
        my_name = config['my_name']
        massoud_user = config['massoud_user']
        devops_user = config['devops_user']
        sobala_user = config['sobala_user']
        call_name_list = config['call_name_list']
        my_phone = config['my_phone']
        sms_alert = config['sms_alert'] == 'true'

        global kavenegar_api
        with open(credentials_path, 'r') as f:
            username = f.readline().strip()
            password = f.readline().strip()
            kavenegar_api = KavenegarAPI(f.readline().strip())
            sender = f.readline().strip()

        kavenegarParams = {
            'receptor': my_phone,
            'message': 'از اسنپ فود پیام دارید',
            'sender': sender
        }

        sk = Skype(connect=False)
        sk.conn.setTokenFile(token_path)
        try:
            sk.conn.readToken()
        except SkypeAuthException:
            sk.conn.setUserPwd(username, password)
            sk.conn.getSkypeToken()

        skEvent = MySkype(tokenFile=token_path, autoAck=True)

        pygame.mixer.init()
        pygame.mixer.music.load(snapp_path)

        image = Image.open(logo_path)
        menu = (pystray.MenuItem('Exit', lambda icon, item: exit_action(icon, item, skEvent)),)
        icon = pystray.Icon("name", image, "My System Tray Icon", menu)

        threading.Thread(target=skEvent.loop).start()

        icon.run(setup)

    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        start()


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

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

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)

api = KavenegarAPI('4B706C6344507A34357361326F3344536D624B7038364D3763657237464744797A696B4F794E372F76576F3D')
params = {'sender': '2000500666', 'receptor': '09024809750', 'message': 'از اسنپ فود پیام دارید'}

my_name = '@Amir Shirdel - Search & Discovery'
massoud_user = '8:live:.cid.1f14d85cc112d076'
devops_user = '19:84854ad599cb4fa987f46dc4103a7636@thread.skype'
sobala_user = '19:a12cbe66dd104756b641dcafb86c774f@thread.skype'

amir_list = [
    'امیر',
    'امیرشیردل',
    'امیر شیردل',
    'امیرشیردلی',
    'امیر شیردلی',
    'amir',
    'amir shirdel',
    'amir shirdeli',
]

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
                        if check_string_existence(event.msg.plain, amir_list):
                            self.show_message('در مورد شما در گروه دو آپس صحبت شده است', sound=False)

                    if event.msg.userId == sobala_user:
                        if check_string_existence(event.msg.plain, amir_list):
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

        if platform.system() == 'Linux' and sound:
            api.sms_send(params)
        else:
            if sound:
                pygame.mixer.music.play()
            ctypes.windll.user32.MessageBoxW(0, message, "SnappFood Alert", 1)
            if sound:
                pygame.mixer.music.stop()


def check_string_existence(target_string, string_list):
    return any(s in target_string for s in string_list)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
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

        with open(credentials_path, 'r') as f:
            username = f.readline().strip()
            password = f.readline().strip()

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

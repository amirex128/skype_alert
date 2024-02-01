import datetime
from skpy import Skype, SkypeAuthException, SkypeEventLoop, SkypeMessageEvent, SkypeCallEvent
import pygame
import ctypes
from kavenegar import *
import platform
import pystray
from PIL import Image
import threading

api = KavenegarAPI('4B706C6344507A34357361326F3344536D624B7038364D3763657237464744797A696B4F794E372F76576F3D')
params = {'sender': '2000500666', 'receptor': '09024809750', 'message': 'از اسنپ فود پیام دارید'}

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


class MySkype(SkypeEventLoop):
    def __init__(self, *args, **kwargs):
        super(MySkype, self).__init__(*args, **kwargs)
        print("*** SkypeBot - Amir Shirdel ***")

    def onEvent(self, event):
        if isinstance(event, SkypeCallEvent):
            if event.msg.userId == '19:84854ad599cb4fa987f46dc4103a7636@thread.skype':
                self.show_message(event)

        if isinstance(event, SkypeMessageEvent):
            if '@Amir Shirdel - Search & Discovery' in event.msg.plain:
                self.show_message('امیر صدا زده شده است')

            if event.msg.userId == '8:live:.cid.1f14d85cc112d076':
                self.show_message('مسعود پیام داده است')

            if event.msg.userId == '19:84854ad599cb4fa987f46dc4103a7636@thread.skype':
                if '@Masood' in event.msg.plain:
                    self.show_message('مسعود را داخل گروه صدا زدند', private=True)

            if event.msg.userId == '19:84854ad599cb4fa987f46dc4103a7636@thread.skype' or event.msg.userId == '19:a12cbe66dd104756b641dcafb86c774f@thread.skype':
                if check_string_existence(event.msg.plain, amir_list):
                    self.show_message('در مورد امیر صحبت شده است', sound=False)

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


def start():
    with open('credentials.txt', 'r') as f:
        username = f.readline().strip()
        password = f.readline().strip()

    sk = Skype(connect=False)
    sk.conn.setTokenFile("token.txt")
    try:
        sk.conn.readToken()
    except SkypeAuthException:
        sk.conn.setUserPwd(username, password)
        sk.conn.getSkypeToken()

    skEvent = MySkype(tokenFile="token.txt", autoAck=True)

    # Create a system tray icon
    image = Image.open("logo.png")  # Replace "icon.png" with the path to your icon
    tray = pystray.Icon("name", image)

    # Define the action to take when the tray icon is clicked
    def on_click(icon, action):
        icon.stop()
        exit(0)

    # Set the tray icon's menu
    tray.menu = pystray.Menu(pystray.MenuItem("Exit", on_click))

    # Run the system tray icon
    threading.Thread(target=tray.run).start()
    threading.Thread(target=skEvent.loop).start()
    exit(0)


if __name__ == '__main__':
    pygame.mixer.init()
    pygame.mixer.music.load('snapp.mp3')
    start()

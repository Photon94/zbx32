import time
from machine import Pin
import network
import utime
import os
import json
import random

# startup indication
led = Pin(27, Pin.OUT)


def boot_indication():
    for _ in range(3):
        led.on()
        utime.sleep(0.2)
        led.off()
        utime.sleep(0.1)


boot_indication()


def enable_ap_mode_indication():
    for _ in range(3):
        led.on()
        utime.sleep(0.2)
        led.off()
        utime.sleep(0.4)


def try_connect_indication():
    led.on()
    utime.sleep(0.5)
    led.off()
    utime.sleep(0.5)


if 'esp.id' not in os.listdir():
    f = open('esp.id', 'w')
    id_ = []
    for _ in range(4):
        id_.append(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'))
    espid = ''.join(id_)
    f.write(espid)
    f.close()
else:
    f = open('esp.id')
    espid = f.read()


ssid = 'zbx32-ap-%s' % espid
password = '123456789'


def enable_ap_mode():
    time.sleep(1)
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password)
    enable_ap_mode_indication()


def do_connect(wlan):
    if not wlan.isconnected():
        print('connecting to network...')
        counter = 0
        while not wlan.isconnected():
            print('.', end='')
            try_connect_indication()
            counter += 1
            if counter >= 10:
                break
    print()
    return wlan.isconnected()


# если есть файл настроек сети network.conf берем оттуда сеть, если его нет то включаем точку доступа и ждем
# передачи настроек
if 'network.conf' in os.listdir():
    print('Try read network.conf')
    conf = open('network.conf')
    try:
        conf = json.loads(conf.read())
        if 'ssid' in conf and 'password' in conf:
            print('Try connect to network')
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            wlan.connect(conf['ssid'], conf['password'])
            if do_connect(wlan):
                print('Connection successful')
                print(wlan.ifconfig())
            else:
                print('Connection error, AP Mode')
                enable_ap_mode()
        else:
            os.remove('network.conf')
            print('Invalid network.conf, remove')
    except Exception:
        print('Config invalid')
        os.remove('network.conf')
else:
    print('Network config not found')
    enable_ap_mode()

import json
from machine import Pin, SoftI2C
from microWebSrv import MicroWebSrv
import ahtx0
import network
import re
from boot import do_connect, enable_ap_mode, try_connect_indication, espid

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
led = Pin(27, Pin.OUT)
led_status = False

sensor = ahtx0.AHT10(i2c)

print("\nTemperature: %0.2f C" % sensor.temperature)
print("Humidity: %0.2f %%" % sensor.relative_humidity)


@MicroWebSrv.route('/temperature')
def temperature(httpClient, httpResponse):
    httpResponse.WriteResponseOk(headers=None, contentType="application/json", contentCharset="UTF-8",
                                 content='{"temperature": %.2f}' % sensor.temperature)


@MicroWebSrv.route('/humidity')
def humidity(httpClient, httpResponse):
    httpResponse.WriteResponseOk(headers=None, contentType="application/json", contentCharset="UTF-8",
                                 content='{"humidity": %.2f}' % sensor.relative_humidity)


@MicroWebSrv.route('/locator')
def locator(httpClient, httpResponse):
    global led_status, led
    if not led_status:
        led.on()
        led_status = True
    else:
        led.off()
        led_status = False
    httpResponse.WriteResponseJSONOk({'locator': led_status, 'esp_id': espid})


def parse_ssid_and_password(data):
    data_: str = data[10:]
    ssid = data_[:data_.index('\r')]
    pwd_start = data_.index('password"\r\n\r\n') + 13
    password = data_[pwd_start:data_[data_.index('password"\r\n\r\n'):].index('\r')+pwd_start-1]
    return ssid, password


@MicroWebSrv.route('/network', 'POST')
def network_(http_client, http_response):
    form_data = http_client.ReadRequestPostedFormData()
    try:
        print('Try ssid and password parsing')
        form_data_ = list(form_data.items())[0][1]
        ssid, password = parse_ssid_and_password(form_data_)
        print(ssid, password)
        http_response.WriteResponseJSONOk({'ssid': ssid, 'password': password})

        print('Try connection')
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(ssid, password)

        do_connect(wlan)

        if not wlan.isconnected():
            print('Connection error, timeout, AP mode enabled')
            enable_ap_mode()
        else:
            conf = open('network.conf', 'w')
            conf.write(json.dumps({'ssid': ssid, 'password': password}))
            print('Config was updated!')
            print('network config:', wlan.ifconfig())
            conf.close()

    except IndexError:
        http_response.WriteResponseJSONError(400, {'error': 'expect form data with ssid and password fields'})
        print(form_data)
    except Exception as e:
        http_response.WriteResponseJSONError(500, {'error': 'internal error'})
        print(form_data)
        raise e



mws = MicroWebSrv()  # TCP port 80 and files in /flash/www
mws.Start(threaded=True)  # Starts server in a new thread

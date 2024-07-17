import storage, wifi
from secrets import secrets

print('SleePi Panda v1.0 by Jinyah\n')

if secrets['hidden']:
    storage.disable_usb_drive()
    print('USB drive features disabled, see /secrets.py for details\n')
else:
    storage.enable_usb_drive()
    print('USB drive features enabled, see /secrets.py for details\n')

if secrets['ssid'] != '' and secrets['password'] != '':
    try:
        wifi.radio.connect(secrets['ssid'], secrets['password'])
    except Exception as e:
        pass

    print('The webserver is hosted at: http://%s' % wifi.radio.ipv4_address)
    
else:
    print('Wi-Fi information not present, please see /secrets.py for details')
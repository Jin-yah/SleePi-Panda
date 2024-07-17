import time
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
import wifi
import socketpool
import adafruit_requests
from secrets import secrets

# Sleep during computer boot
time.sleep(30)

# Setup the onboard LED for indicating the toggle state
try:
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
except Exception as e:
    led = False

# Global variables
run = True
toggle = True
led.value = True
last_pressed = 0
keypress_interval = 10

# Custom Keycode for F13, which will wake the computer without affecting normal use
F13 = 0x68

# Create a Keyboard object to send key presses over USB HID
keyboard = Keyboard(usb_hid.devices)


# Main function to handle the toggle and serve the web interface
def server_run():
    global run, toggle, last_pressed
    
    # Load HTML templates for the "on" and "off" states
    html_on = load_html("/html/html_on.html")
    html_off = load_html("/html/html_off.html")
    
    # Connect to WiFi if not already connected
    if not wifi.radio.connected:
        try:
            wifi.radio.connect(secrets['ssid'], secrets['password'])
        except Exception as e:
            print('WiFi connection error:', e)

    # Create a SocketPool and Requests Session for network communication
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool)

    # Setup the web server on port 80
    socket = pool.socket()
    socket.settimeout(1)
    socket.setsockopt(pool.SOL_SOCKET, pool.SO_REUSEADDR, 1)
    socket.bind(('0.0.0.0', 80))
    socket.listen(1)

    print('http://%s' % wifi.radio.ipv4_address)

    # Main loop to handle HTTP requests and send key inputs
    while run:
        try:
            # Wait for a client to connect
            conn, addr = socket.accept()
            print('Client connected from', addr)

            # Use recv_into to receive data into a buffer
            buffer = bytearray(1024)
            num_bytes = conn.recv_into(buffer, len(buffer))

            # Decode received bytes into a string
            request = buffer[:num_bytes].decode('utf-8')

            # Check if the request is to turn the toggle "on"
            if 'POST /on' in request:
                toggle = True
                toggle_led()

            # Check if the request is to turn the toggle "off"
            elif 'POST /off' in request:
                toggle = False
                toggle_led()

            elif 'POST /stop' in request:
                toggle = False
                if led:
                    led.value = False
                run = False

            # Select the appropriate HTML response based on the toggle state
            if toggle:
                response = html_on
            else:
                response = html_off

            # Send HTTP response headers and content
            conn.sendall(b'HTTP/1.1 200 OK\n')
            conn.sendall(b'Content-Type: text/html\n')
            conn.sendall(b'Connection: close\n\n')
            conn.sendall(response.encode('utf-8'))

            # Close the connection to the client
            conn.close()

        except OSError as e:
            pass

        # Check if the toggle is active and if enough time has passed since the last key press
        if toggle and (time.monotonic() - last_pressed >= keypress_interval):
            # Send the F13 key press
            keyboard.press(F13)
            time.sleep(0.1)
            keyboard.release(F13)  # Ensure the key is released
            last_pressed = time.monotonic()  # Update the timestamp of the last key press

        # Short delay to avoid excessive CPU usage
        time.sleep(0.1)
    socket.close()
    print("Shutting down")


# Backup script without wifi capabilities to keep computer awake
def run_backup():
    global last_pressed
    
    led.value = False
    
    while True:
        if time.monotonic() - last_pressed >= keypress_interval:
            # Send the F13 key press
            toggle_led()
            keyboard.press(F13)
            time.sleep(0.1)
            keyboard.release(F13)  # Ensure the key is released
            toggle_led()
            last_pressed = time.monotonic()  # Update the timestamp of the last key press
        
        time.sleep(0.1)


# Function to load HTML templates from files
def load_html(filename):
    try:
        with open(filename, "r") as file:
            return file.read()
    except OSError:
        return "<html><body><h1>Error loading template</h1></body></html>"

def toggle_led():
    if led:
        led.value = False if led.value else True


# Check if wifi is set up and run correct script
if secrets['ssid'] == '' or secrets['password'] == '':
    run_backup()
else:
    server_run()

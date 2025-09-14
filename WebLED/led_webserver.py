import network
import socket
from time import sleep
from picozero import pico_temp_sensor, pico_led
import machine
import rp2
import sys

ssid = "NotTheRealSSID"
password = "NotThePassword"


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        if rp2.bootsel_button() == 1:
            sys.exit()
        print("Waiting for connection...")
        pico_led.on()
        sleep(0.5)
        pico_led.off()
        sleep(0.5)
        
    ip = wlan.ifconfig()[0]
    # print(wlan.ifconfig())
    print(f'Connected on {ip}')
    pico_led.on()
    return ip


def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    # print(connection)  # socket_state = 1 means it is working
    return connection


def get_webpage(temperature, state):
    #Template HTML
    html = f"""
            <!DOCTYPE html>
            <html>
            <form action="./lighton">
            <input type="submit" value="Light on" />
            </form>
            <form action="./lightoff">
            <input type="submit" value="Light off" />
            </form>
            <p>LED is {state}</p>
            <p>Temperature is {temperature}</p>
            <form action="./close">
            <input type="submit" value="Stop server"/>
            </form>
            </body>
            </html>
            """
    return str(html)


def serve(connection):
    state = 'OFF'
    pico_led.off()
    temperature = 0
    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        # print(request)
        
        try:
            request = request.split()[1]
        except IndexError:
            print("Request split failed:", request)
        if request == '/lighton?':
            pico_led.on()
            state = 'ON'
            print("Turning LED on")
        elif request == '/lightoff?':
            pico_led.off()
            state = 'OFF'
            print("Turning LED off")
        elif request == '/close?':
            print("Taking server down")
            client.close()
            break
        else:
            print("Request[1]:", request)
        
        temperature = pico_temp_sensor.temp
        html = get_webpage(temperature, state)
        client.send(html)
        client.close()
        
        if rp2.bootsel_button() == 1:
            connection.close()
            break
    

ip = connect()
connection = open_socket(ip)
serve(connection)
connection.close()

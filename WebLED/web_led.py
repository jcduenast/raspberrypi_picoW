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


def connect_ap():
    wlan = network.WLAN(network.AP_IF)
    wlan.active(True)
    # wlan.config(essid="Pico_AP", authmode=0)
    wlan.config(essid="Pico_AP", password="12345678")  # crea red WiFi
    # wlan.ifconfig(("10.0.0.1", "255.255.255.0", "10.0.0.1", "10.0.0.1"))  # (ip, netmask, gateway, dns)
    pico_led.on()
    sleep(2)
    ip = wlan.ifconfig()[0]
    print(f"Access Point active. SSID: Pico_AP, IP: {ip}")
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
    try:
        with open("index.html", "r") as f:
            html = f.read()
    except Exception as e:
        html = f"<html><body><h1>Error loading page: {e}</h1></body></html>"
        return html

    # Reemplaza los marcadores por valores reales
    html = html.replace("{{STATE}}", state)
    html = html.replace("{{TEMP}}", f"{temperature:.2f} °C")

    return html


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
            client.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            client.send("<html><body><h1>Server stopped</h1></body></html>")
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


def main():
    # ip = connect()   # connect to an existing network
    ip = connect_ap()   # create an access point
    connection = open_socket(ip)
    serve(connection)
    connection.close()


if __name__ == "__main__":
    main()

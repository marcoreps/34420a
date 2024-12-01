import time,csv,gpib
from datetime import datetime
from paho.mqtt import client as mqtt_client
import json

my_instrument = gpib.find("34420a")
gpib.config(0,gpib.IbcAUTOPOLL,1)  # Enable automatic serial polling
gpib.config(my_instrument,gpib.IbcTMO, gpib.T30s) # Set timeout to 30 seconds


gpib.write(my_instrument,"SYSTem:ERRor?")
print(gpib.read(my_instrument,100))

#gpib.write(my_instrument,"*RST")

gpib.write(my_instrument,"*IDN?")
print(gpib.read(my_instrument,100))

gpib.write(my_instrument,"*CLS")

gpib.write(my_instrument,"CONFigure:VOLTage:DC 0.001, MAX, (@FRONt1)")
gpib.write(my_instrument,"ROUTe:TERMinals FRONt1")
gpib.write(my_instrument,"SENSe:VOLTage:DC:NPLCycles 100")
gpib.write(my_instrument,"INPut:FILTer:STATe OFF")
gpib.write(my_instrument,"TRIGger:DELay 0")

#gpib.write(my_instrument,"OUTPut:STATe OFF")
#gpib.write(my_instrument,"SENSe:NULL ONCE")
gpib.write(my_instrument,"TRIGger:SOURce IMMediate")
gpib.write(my_instrument,"INIT")

gpib.write(my_instrument,"SAMP:COUN 1")

gpib.write(my_instrument,"*SRE 32") # "Standard Event" bit in Status Byte pulls the SRQ line
gpib.write(my_instrument,"*ESE 1") # "Operation Complete" will set "Standard Event" bit in Status Byte

gpib.write(my_instrument,"INIT")
gpib.write(my_instrument,"*OPC")


broker = '192.168.178.27'
port = 1883
topic = "lab_sensors/TMP117"
client_id = f'subscribe-{42}'
TMP117_room_temp = 0.0


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        x = msg.payload.decode()[33:38]
        global TMP117_room_temp
        TMP117_room_temp = float(x)
        print(TMP117_room_temp)

    client.subscribe(topic)
    client.on_message = on_message

client = connect_mqtt()
subscribe(client)
    


timestr = time.strftime("%Y%m%d-%H%M%S_")
counter = 0
try:
    with open('csv/'+timestr+'Keysight_34420a_tempco.csv', mode='w') as csv_file:
        fieldnames = ['time', '34420a_volt', 'TMP117_room_temp']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        clock=datetime.now()
        while True:
            counter += 1
            if counter > 30:
                client = connect_mqtt()
                subscribe(client)
                counter = 0
                
            client.loop()
            sta = gpib.wait(my_instrument, gpib.TIMO | gpib.RQS) # Wait for Timeout or Request Service on device
            #if (sta & gpib.TIMO) != 0:
            #    print("Timed out")
            #else:
            #    print("Device asserted RQS")
                
            gpib.write(my_instrument,"FETC?")
            readings = gpib.read(my_instrument,100)
            gpib.write(my_instrument,"INIT")
            gpib.write(my_instrument,"*OPC")
            reading = readings.decode("utf-8").rstrip()

            writer.writerow({'time':time.time(), '34420a_volt':reading, 'TMP117_room_temp':TMP117_room_temp})

            print("Measured: "+str(reading))
            print("last room temp: "+str(TMP117_room_temp))
            
            
except (KeyboardInterrupt, SystemExit) as exErr:
    gpib.close(my_instrument)
    print("kthxbye")
    sys.exit(0)
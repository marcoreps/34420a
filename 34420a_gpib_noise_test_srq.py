# My usual goto library pyvisa-py doesn't currently implement SRQ support.
# So here I am using the linux-gpib python bindings to react to SRQ states
# and avoid bothering the voltmeter with frequent "done yet?" requests.

import gpib,time,csv,sys
from datetime import datetime

batchsize = 50

my_instrument = gpib.find("34420a")
gpib.config(0,gpib.IbcAUTOPOLL,1)  # Enable automatic serial polling
gpib.config(my_instrument,gpib.IbcTMO, gpib.T30s) # Set timeout to 30 seconds


gpib.write(my_instrument,"SYSTem:ERRor?")
print(gpib.read(my_instrument,100))

gpib.write(my_instrument,"*RST")

gpib.write(my_instrument,"*IDN?")
print(gpib.read(my_instrument,100))

gpib.write(my_instrument,"*CLS")

gpib.write(my_instrument,"DISPlay OFF")

gpib.write(my_instrument,"CONFigure:VOLTage:DC 0.001, MAX, (@FRONt1)")
gpib.write(my_instrument,"ROUTe:TERMinals FRONt1")
gpib.write(my_instrument,"SENSe:VOLTage:DC:NPLCycles 1")
gpib.write(my_instrument,"INPut:FILTer:STATe OFF")
gpib.write(my_instrument,"TRIGger:DELay 0")

gpib.write(my_instrument,"OUTPut:STATe OFF")
gpib.write(my_instrument,"SENSe:NULL ONCE")
gpib.write(my_instrument,"TRIGger:SOURce IMMediate")
gpib.write(my_instrument,"INIT")

gpib.write(my_instrument,"SAMP:COUN "+str(batchsize))

gpib.write(my_instrument,"*SRE 32") # "Standard Event" bit in Status Byte pulls the SRQ line
gpib.write(my_instrument,"*ESE 1") # "Operation Complete" will set "Standard Event" bit in Status Byte

gpib.write(my_instrument,"INIT")
gpib.write(my_instrument,"*OPC")

timestr = time.strftime("%Y%m%d-%H%M%S_")

try:
    with open('csv/'+timestr+'Keysight_34420A_short_NPLC1.csv', mode='w') as csv_file:
        fieldnames = ['time', '34420a_volt']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        clock=datetime.now()
        batches = 0
        while True:
            sta = gpib.wait(my_instrument, gpib.TIMO | gpib.RQS) # Wait for Timeout or Request Service on device
            if (sta & gpib.TIMO) != 0:
                print("Timed out")
            else:
                print("Device asserted RQS")
                
            gpib.write(my_instrument,"FETC?")
            readings = gpib.read(my_instrument,1000)
            gpib.write(my_instrument,"INIT")
            gpib.write(my_instrument,"*OPC")
            readings = readings.decode("utf-8").rstrip()
            readings = readings.split(",")
            #print(readings)
            
            for val in readings:
                writer.writerow({'time':time.time(), '34420a_volt': float(val)})

            batches = batches+1

            print("Batches received: "+str(batches))
            print("Script runtime seconds: "+str((datetime.now()-clock).total_seconds()))
            print("Effective readings per second: "+str(batchsize*batches/(datetime.now()-clock).total_seconds()))
            
            
except (KeyboardInterrupt, SystemExit) as exErr:
    gpib.close(my_instrument)
    print("kthxbye")
    sys.exit(0)
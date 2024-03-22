import pyvisa,time,csv
#from datetime import datetime
from pyvisa.constants import StopBits, Parity
rm = pyvisa.ResourceManager()
my_instrument = rm.open_resource('ASRL/dev/ttyUSB0::INSTR',baud_rate=9600, data_bits=8,stop_bits=StopBits.two,write_termination='\n',read_termination='\n',parity=Parity.none)
my_instrument.timeout = 20000
my_instrument.write('*RST')
my_instrument.write('SYSTem:REMote')
time.sleep(3)
print(my_instrument.query('*IDN?'))
print(my_instrument.query('SYSTem:ERRor?'))
my_instrument.write("DISPlay OFF")

my_instrument.write("CONFigure:VOLTage:DC 0.001, MAX, (@FRONt1)")
my_instrument.write("ROUTe:TERMinals FRONt1")
my_instrument.write("SENSe:VOLTage:DC:NPLCycles 100")
my_instrument.write("INPut:FILTer OFF")
my_instrument.write("TRIGger:DELay 0")

my_instrument.write("SENSe:NULL ONCE")

my_instrument.write("TRIGger:SOURce IMMediate")



timestr = time.strftime("%Y%m%d-%H%M%S_")
with open('csv/'+timestr+'HP_34420A_short_NPLC100.csv', mode='w') as csv_file:
    fieldnames = ['time', '34420a_volt']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    #clock=datetime.now()
    while True:
        val = float(my_instrument.query("READ?"))
        writer.writerow({'time':time.time(), '34420a_volt': val})
        print(val)
        #print( "Real NPLC: "+str((datetime.now()-clock).total_seconds()/0.02))
        #clock=datetime.now()
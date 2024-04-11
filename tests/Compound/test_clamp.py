# %%
import serial

from controllably import Helper

Helper.get_ports()
# %%
device = serial.Serial('COM18', 115200, timeout=1)
# %%
device.read_all()
while True:
    try:
        response = device.readline()
        print(response)
    except KeyboardInterrupt:
        break
# %%
device.write('H 0\n'.encode())
# %%
device.write('G -10\n'.encode())
# %%

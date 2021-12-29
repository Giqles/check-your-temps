import time
import regex as re
import serial
import warnings
from serial.tools import list_ports
import clr
clr.AddReference('OpenHardwareMonitorLib')
from OpenHardwareMonitor.Hardware import Computer
from statistics import mean

def initialize_handler():
    pc = Computer()
    pc.CPUEnabled = True
    pc.GPUEnabled = True
    pc.Open()
    return pc

# Is this documented anywhere?
TEMP_SENSOR = 2

def pull_data(handle):
    gpu_temps = []
    cpu_temps = []
    for i in handle.Hardware:
        i.Update()
        for sensor in i.Sensors:
            if sensor.SensorType == TEMP_SENSOR:
                if re.match(r'CPU', sensor.Name):
                    cpu_temps.append(sensor.Value)
                if re.match(r'GPU', sensor.Name):
                    gpu_temps.append(sensor.Value)

    # average or None
    if len(cpu_temps) > 0:
        cpu_temp = f'{mean(cpu_temps):.1f}'
    elif len(cpu_temps) == 0:
        cpu_temp = None

    if len(gpu_temps) > 0:
        gpu_temp = f'{mean(gpu_temps):.1f}'
    elif len(gpu_temps) == 0:
        gpu_temp = None

    return cpu_temp, gpu_temp

def get_port(max_attempts=15):
    attempts = 0
    while attempts <= max_attempts:
        ports = list_ports.comports()
        # VID:PID in hex for Pi Pico should be 2E8A:0005
        # position 2 of the ListPort object is the hardware ID info
        pico_ports = list(filter(lambda x: re.search(r'2E8A:0005', x[2]), ports))
        if len(pico_ports) == 0:
            if attempts <= max_attempts:
                warnings.warn('Pi Pico not found. Waiting for 20 seconds then trying again.')
                time.sleep(20)
                attempts += 1
                continue
            elif attempts > max_attempts:
                raise Exception(f'Pi Pico not found after {attempts} tries.')
        elif len(pico_ports) > 0:
            if len(pico_ports) > 1:
                warnings.warn('Multiple Pi Pico found. Using first one.')
            return pico_ports[0][0]

def send_and_receive(conn, cpu, gpu, wait_for_response=False):
    command = f"{cpu} {gpu}" + r"\n"
    encoded_command = bytes(command.replace('\\n', '\n').encode('utf-8'))
    conn.write(encoded_command)
    # this is really only for debugging
    if wait_for_response:
        while conn.inWaiting() > 0:
            pico_reply = conn.readline()
            print(pico_reply.decode("utf-8", "ignore"))
            time.sleep(0.01)


if __name__=='__main__':
    try:
        # open the handler for pc temp data
        pc = initialize_handler()
        # loop forever pulling temp data and sending it to the pico
        while True:
            cpu, gpu = pull_data(pc)
            port = get_port()
            ser = serial.Serial(port)
            send_and_receive(ser, cpu, gpu)
            ser.close()
            time.sleep(1)
    except KeyboardInterrupt:
        if ser != None:
            ser.close()

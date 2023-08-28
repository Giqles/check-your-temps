import time
import regex as re
import serial
import warnings
from serial.tools import list_ports
import clr
clr.AddReference('OpenHardwareMonitorLib')
from OpenHardwareMonitor.Hardware import Computer, SensorType
from statistics import mean

def initialize_handler():
    pc = Computer()
    pc.CPUEnabled = True
    pc.GPUEnabled = True
    pc.MainboardEnabled = True
    pc.Open()
    return pc

# Is this documented anywhere?
TEMP_SENSOR = 2

def get_temperatures(hardware_item, sensor_data=[]):
    """
    Recursively pull hardware temperature sensors from the OpenHardwareMonitor
    """
    hardware_item.Update()
    for sensor in hardware_item.Sensors:
        if sensor.SensorType == SensorType.Temperature and sensor.Value is not None:
            sensor_data.append({'name': sensor.Name, 'sensorType': sensor.SensorType, 'value': sensor.Value})
    
    for sub_hw in hardware_item.SubHardware:
        sub_hw.Update()
        get_temperatures(sub_hw)

    return sensor_data

def pull_data(handle):

    def _get_average(temps):
        if len(temps) > 0:
            return f"{mean(temps):.1f}"
        else:
            return None

    all_temps = []
    for hw in handle.Hardware:
        all_temps.extend(get_temperatures(hw))

    cpu = [x['value'] for x in all_temps if 'CPU' in x['name'].upper()]
    gpu = [x['value'] for x in all_temps if 'GPU' in x['name'].upper()]
    
    return _get_average(cpu), _get_average(gpu)

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
            print(f'CPU: {cpu} GPU: {gpu}')
            port = get_port()
            ser = serial.Serial(port)
            send_and_receive(ser, cpu, gpu)
            ser.close()
            time.sleep(1)
    except KeyboardInterrupt:
        if ser != None:
            ser.close()

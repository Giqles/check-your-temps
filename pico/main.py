import utime
import random
import sys
import select
from OLED import OLED_1inch3

INCREMENT = 0.1

OLED = OLED_1inch3()

OLED.fill(OLED.black)
OLED.text("Starting up", 1, 10, OLED.white)
OLED.show()

received_data = False
time_since_last_update = 0
has_shutdown = False

while True:
    if select.select([sys.stdin], [], [], 0)[0]:
        print('receiving data')
        data = sys.stdin.readline()
        print(f'received: {data}')
        
        # prep data
        received_data = True
        data = data.split()
        cpu = data[0]
        gpu = data[1]
        
        # update display        
        OLED.fill(OLED.black)
        
        if cpu != 'None':
            OLED.text(f'CPU Temp: {cpu}C', 1, 10, OLED.white)
        else:
            OLED.text(f'CPU data not found.', 1, 10, OLED.white)
        
        if gpu != 'None':
            OLED.text(f'GPU Temp: {gpu}C', 1, 27, OLED.white)
        else:
            OLED.text(f'GPU data not found.', 1, 27, OLED.white)
            
        OLED.show()
        
        time_since_last_update = 0
        has_shutdown = False
        
    else:
        print('Waiting for data')
        
        time_since_last_update += INCREMENT
        
        if not received_data:
            OLED.fill(OLED.black)
            OLED.text('Waiting for data.', 1, 10, OLED.white)
            OLED.show()
            
        elif time_since_last_update > 5 and not has_shutdown:
            OLED.fill(OLED.black)
            OLED.text('No data for > 5s.', 1, 10, OLED.white)
            OLED.text('Shutting down.', 1, 27, OLED.white)
            OLED.show()
            
            utime.sleep(5)
            OLED.fill(OLED.black)
            OLED.show()
            
            has_shutdown = True
        
    utime.sleep(INCREMENT)


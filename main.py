import win32file
import win32api
import win32con
import struct
import time
from datetime import datetime, timedelta

def handle_device_add(device_path, device_id, product_id):
    # Open the input device
    h_input_device = win32file.CreateFile(
        device_path,
        win32con.GENERIC_READ | win32con.GENERIC_WRITE,
        0, None, win32con.OPEN_EXISTING, 0, None
    )

    # Set the input device's sharing mode to share read access
    win32file.SetCommMask(h_input_device, win32con.EV_RXCHAR)
    win32file.SetCommState(h_input_device, win32file.DCB(ByteSize=8, BaudRate=115200, Flags=win32file.fBinary, fRtsControl=1))
    win32file.SetCommTimeouts(h_input_device, win32file.COMMTIMEOUTS(ReadIntervalTimeout=250))
    
    # Get timezone offset
    now = datetime.now()
    offset = now.utcoffset()

    if offset is not None:
        # Format the offset as a string
       offset_str = '{:+03d}:{:02d}'.format(offset.seconds // 3600, (offset.seconds // 60) % 60)
    else:
        offset_str = '+00:00'

    # Start logging input
    with open('input.log', 'a') as log_file:
        while True:
            # Read an input event
            event = win32file.ReadFile(h_input_device, 32)

            # Parse the input event
            event_struct = struct.unpack('LLHHI', event[1])
            event_type = event_struct[0]
            event_code = event_struct[1]
            event_value = event_struct[2]

            # Format the input event as a string
            timestamp = time.strftime("%d%m%Y %H:%M:%S.%f", time.gmtime(), offset_str)
            event_str = '{} {} {} {} {} {}'.format(timestamp, device_id, product_id, event_type, event_code, event_value)

            # Write the event to the log file and standard output
            log_file.write('{}\n'.format(event_str))
            print(event_str)

def start_monitoring():
    # Get a list of all USB devices
    devices = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
    usb_devices = [d for d in devices if d.startswith('\\')]

    # Keep track of the devices that have been logged
    logged_devices = set()

    while True:
        # Get a list of newly added USB devices
        new_devices = set(usb_devices) - logged_devices

        # Handle each new device
        for device_path in new_devices:
            # Get the device's ID and product ID
            device_id = win32api.GetVolumeInformation(device_path)[4]
            product_id = win32api.GetVolumeInformation(device_path)[5]

            # Log the input from the device
            handle_device_add(device_path, device_id, product_id)
            logged_devices.add(device_path)

if __name__ == '__main__':
    start_monitoring()

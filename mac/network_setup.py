"""

This module acts as a wrapper for the OSX command line utility networksetup.

Attributes:
    LOGGER (logging.Logger): Module level variable used to capture logging staments.

"""

import subprocess
import logging
import re

LOGGER = logging.getLogger(__name__)
__author__ = 'John Mezzanotte'


def run(**kwargs):

    """
    Launches networksetup CLI with given commands.

    :param options: (list) - A list of commands to be passed to networksetup process.
    :return: (tuple) - Returns stdout, stderr, and error code from given process in a tuple.
    """

    cmd = ['networksetup']
    options = kwargs.get('options', [])

    LOGGER.info("Running networksetup.")
    LOGGER.info("Commands: %s", cmd + options)

    process = subprocess.Popen(cmd + options, stdout=subprocess.PIPE, stderr=subprocess.PIPE,)

    stdout, stderr = process.communicate()
    error_code = process.returncode
    LOGGER.debug("networksetup finished with error code %s", error_code)

    return stdout, stderr, error_code


def power_on(device):
    """
    Turns on wifi port.
    :param device: (str) Name of device.
    :return: (boolean) - True if the device was turned on false otherwise.
    """
    return _set_airport_power(device)


def power_off(device):
    """
    Turns off wifi device
    :param device: (str) Name of device.
    :return: (boolean) True if the device was turned off false otherwise.
    """
    return _set_airport_power(device, on=False)


def _set_airport_power(device, on=True):
    """
    Will turn on wifi device.
    :param device: (str) - Name of device
    :param on: (boolean) True to turn device on, False to turn it off.
    :return: (boolean) True if command was successfull.
    """

    if not device:
        LOGGER.error("Please provide an airport device to turn on.")
        return False

    power = 'On' if on else 'Off'

    LOGGER.info('Turning %s power for device %s', power, device)
    process = run(options=['-setairportpower', '{}'.format(device), '{}'.format(power)])
    stdout = process[0]
    error_code = process[-1]
    LOGGER.info(stdout)

    if error_code > 0:
        LOGGER.error("Unable to turn on airport device %s", device)
        return False

    return True


def get_devices():

    """
    Get all network hardware ports
    :return: (dict) A dictionary with all hardware devices.
    """
    ret_dict = {}
    stdout = run(options=['-listallhardwareports'])[0]

    if stdout:

        pattern = re.compile(r'([A-Za-z\s-]*)([:])\s([A-Za-z:0-9\s/-]*)')
        device_name_pattern = re.compile(r'Hardware Port:\s([A-Za-z0-9-\s]*)\n')
        stdout = stdout.strip()
        devices = stdout.split('\n\n')
        ret_dict = {}

        for index, device in enumerate(devices):

            key = re.match(device_name_pattern, device)

            if key:
                key = key.group(1)
                temp = {key: {}}

                for target_device in devices[index].splitlines():
                    find = re.match(pattern, target_device)

                    if find:

                        temp[key].update({find.group(1) : find.group(3)})

                        ret_dict.update(temp)

    return ret_dict


def get_wifi_device():
    """
    Retrieves all Wifi devices on the system.
    :return: (dict) A dictionary containing wifi devices connected to the system.
    """
    return get_devices().get('Wi-Fi', None) if get_devices() else None


def get_network(device):
    """
    Retrieves the name of the network that is currently connected to wifi device.
    :param device: (str) Name of wifi device
    :return: (str) The name of the connected network, None otherwise.
    """
    ret_val = None
    if not device:
        LOGGER.error("No device given.")
        ret_val = None

    stdout = run(options=['-getairportnetwork', device])[0]

    if stdout:
        pattern = re.compile(r'[A-Za-z-\s]*:\s([A-Za-z.\'\s_-]*)')
        LOGGER.info(stdout)
        result = re.match(pattern, stdout)
        if result:
            ret_val = result.group(1).strip()

    return ret_val


def connect(wifi_device, network_name, password):

    """
    Connects to a wifi network.
    :param wifi_device: (str) - Wifi device name
    :param network_name: (str) - Network name
    :param password: (str) - Network password
    :return: (boolean) - True if connected, False otherwise.
    """

    stdout = run(options=['-setairportnetwork', '{}'.format(wifi_device), '{}'.format(network_name),
                          '{}'.format(password)])

    # If there is data in stdout, this means we failed to connect.
    if stdout:
        if 'Failed' in stdout:
            LOGGER.error(stdout)
            return False

    return True


def get_computer_name():

    """
    Gets the hostname of the system.
    :return: (str) - hostname of the system.
    """
    return run(options=['-getcomputername'])[0]


if __name__ == "__main__":
    FORMAT_STR = '%(asctime)-15s - %(levelname)s - %(name)s - %(module)s - %(message)s'
    STREAM_HANDLER = logging.StreamHandler(FORMAT_STR)
    FORMATTER = logging.Formatter()
    STREAM_HANDLER.setFormatter(FORMATTER)
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(STREAM_HANDLER)


    print get_wifi_device()
    power_on(get_wifi_device().get('Device'))


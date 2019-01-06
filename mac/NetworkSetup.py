import subprocess
import logging
import re

logger = logging.getLogger(__name__)
__author__ = 'John Mezzanotte'


def run(**kwargs):

    cmd = ['networksetup']
    options = kwargs.get('options', [])

    logger.info("Running networksetup.")
    logger.info("Commands: {}".format(cmd + options))

    process = subprocess.Popen(cmd + options, stdout=subprocess.PIPE, stderr=subprocess.PIPE,)

    stdout, stderr = process.communicate()
    error_code = process.returncode
    logger.debug("networksetup finished with error code {}".format(error_code))

    return stdout, stderr, error_code


def power_on(device):
    return _set_airport_power(device)


def power_off(device):
    return _set_airport_power(device, on=False)


def _set_airport_power(device, on=True):

    if not device:
        logger.error("Please provide an airport device to turn on.")
        return False

    power = 'On' if on else 'Off'

    logger.info('Turning {0} power for device {1}'.format(power, device))
    stdout, stderr, error_code = run(options=['-setairportpower', '{}'.format(device), '{}'.format(power)])
    logger.info(stdout)

    if error_code > 0:
        logger.error("Unable to turn on airport device {}".format(device))
        return False

    return True


def get_devices():

    ret_dict = {}
    stdout, stderr, error_code = run(options=['-listallhardwareports'])

    if stdout:

        pattern = re.compile(r'([A-Za-z\s-]*)([:])\s([A-Za-z:0-9\s/-]*)')
        device_name_pattern = re.compile(r'Hardware Port:\s([A-Za-z0-9-\s]*)\n')
        stdout = stdout.strip()
        devices = stdout.split('\n\n')
        ret_dict = {}

        for device_index in range(0, len(devices)):

            key = re.match(device_name_pattern, devices[device_index])

            if key:
                key = key.group(1)
                temp = {key: {}}

                for device in devices[device_index].splitlines():
                    find = re.match(pattern, device)

                    if find:

                        temp[key].update({find.group(1) : find.group(3)})

                        ret_dict.update(temp)

    return ret_dict


def get_wifi_device():

    return get_devices().get('Wi-Fi', None) if get_devices() else None


def get_network(device):

    ret_val = None
    if not device:
        logger.error("No device given.")
        ret_val = None

    stdout, stderr, error_code = run(options=['-getairportnetwork', device])

    if stdout:
        pattern = re.compile(r'[A-Za-z-\s]*:\s([A-Za-z.\'\s_-]*)')
        logger.info(stdout)
        result = re.match(pattern, stdout)
        if result:
            ret_val = result.group(1).strip()

    return ret_val


def connect(wifi_device, network_name, password):

    stdout, stderr, error_code = run(options=['-setairportnetwork',
                                              '{}'.format(wifi_device),
                                              '{}'.format(network_name),
                                              '{}'.format(password)])

    # If there is data in stdout, this means we failed to connect.
    if stdout:
        if 'Failed' in stdout:
            logger.error(stdout)
            return False

    return True


if __name__ == "__main__":

    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)-15s - %(levelname)s - %(name)s - %(module)s - %(message)s')
    stream_handler.setFormatter(formatter)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)


    print get_wifi_device()
    #print get_airport_network(get_wifi_device()['Device'])
    power_on(get_wifi_device().get('Device'))
    #print set_airport_network(get_wifi_device()['Device'], 'JohnsNetwork', 'midnightPrunes2$h')

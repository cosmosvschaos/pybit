import time
import re
import copy
import logging
from functools import lru_cache

@lru_cache(maxsize=1)
def get_server_time_delay(session):
    """
    Fetch the Bybit server time and calculate the delay between the server time and the system time.

    :param session: The session object used to communicate with the Bybit API.
    :return: The delay in nanoseconds.
    """
    try:
        response = session.get_server_time()
        if response['retCode'] == 0:
            server_time_nano = int(response['result']['timeNano'])
            system_time_nano = int(time.time() * 1e9)
            delay = server_time_nano - system_time_nano
            logging.info(f"Calculated delay: {delay} nanoseconds")
            return delay
        else:
            error_message = f"Error retrieving Bybit server time: {response['retMsg']}"
            logging.error(error_message)
            raise Exception(error_message)
    except Exception as e:
        error_message = f"Error retrieving Bybit server time: {e}"
        logging.error(error_message)
        raise

def generate_req_timestamp(session):
    """
    Generate a request timestamp.

    :param session: The session object used to communicate with the Bybit API.
    :return: The request timestamp in milliseconds.
    """
    def get_current_utc_milliseconds():
        """Returns the current UTC time in milliseconds since the epoch."""
        epoch_time = time.time()
        return int(epoch_time * 1000)

    try:
        if session:
            try:
                delay_nano = get_server_time_delay(session)
                current_system_time_nano = int(time.time() * 1e9)
                server_time_nano = current_system_time_nano + delay_nano
                return server_time_nano // 1000000  # Convert nanoseconds to milliseconds
            except Exception:
                logging.error("Failed to get server time delay, falling back to UTC time.")
        
        # If there's no session or server time delay retrieval failed, use current UTC time
        print("No session available, using UTC time as req_timestamp")
        return get_current_utc_milliseconds()

    except Exception as e:
        utc_milliseconds = get_current_utc_milliseconds()
        logging.error(f"Error generating req_timestamp: {e}, using UTC time: {utc_milliseconds}")
        print(f"Error generating req_timestamp: {e}")

        return utc_milliseconds  # Or another meaningful return value, as needed

def generate_timestamp():
    """
    Return a millisecond integer timestamp.
    """
    return int(time.time() * 10**3)


def identify_ws_method(input_wss_url, wss_dictionary):
    """
    This method matches the input_wss_url with a particular WSS method. This
    helps ensure that, when subscribing to a custom topic, the topic
    subscription message is sent down the correct WSS connection.
    """
    path = re.compile("(wss://)?([^/\s]+)(.*)")
    input_wss_url_path = path.match(input_wss_url).group(3)
    for wss_url, function_call in wss_dictionary.items():
        wss_url_path = path.match(wss_url).group(3)
        if input_wss_url_path == wss_url_path:
            return function_call


def find_index(source, target, key):
    """
    Find the index in source list of the targeted ID.
    """
    return next(i for i, j in enumerate(source) if j[key] == target[key])


def make_private_args(args):
    """
    Exists to pass on the user's arguments to a lower-level class without
    giving the user access to that classes attributes (ie, passing on args
    without inheriting the parent class).
    """
    args.pop("self")
    return args


def make_public_kwargs(private_kwargs):
    public_kwargs = copy.deepcopy(private_kwargs)
    public_kwargs.pop("api_key", "")
    public_kwargs.pop("api_secret", "")
    return public_kwargs


def are_connections_connected(active_connections):
    for connection in active_connections:
        if not connection.is_connected():
            return False
    return True


def is_inverse_contract(symbol: str):
    if re.search(r"(USD)([HMUZ]\d\d|$)", symbol):
        return True


def is_usdt_perpetual(symbol: str):
    if symbol.endswith("USDT"):
        return True


def is_usdc_perpetual(symbol: str):
    if symbol.endswith("USDC"):
        return True


def is_usdc_option(symbol: str):
    if re.search(r"[A-Z]{3}-.*-[PC]$", symbol):
        return True

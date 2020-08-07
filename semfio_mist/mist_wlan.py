from semfio_mist.logger import logger, logger_engine
from semfio_mist.config import Config
from semfio_mist.mist_api import API


class WLAN:
    """Mist WLAN Object
    """

    wlan_id: str = None
    ssid: str
    site_id: str
    api: API
    band: str = None
    interface: str = None
    hostname_ie: str = None
    auth: dict = None
    auth_servers: list = None
    roam_mode: str = None
    rateset: dict = None

    def __init__(self, ssid: str, site_id: str, api: API, wlan_config: dict, *args, **kwargs):
        """Initializes the Mist WLAN instance

        Initialize the following object attributes:
            ssid: a str defining the ssid (or name) of the WLAN profile
            site_id: a str defining the site_id if the site already exists on the Mist cloud
            api: a API object that contains all the necessary methos to perform API calls
            config: a Config object containing the content of the config file

        This method validates if the WLAN already exists on the Mist cloud based on its name
        If it does, the local attributes are configued via the _does_exist_on_cloud methd.
        If it doesn not, this function configured the attributes using the data provided in the config file
        """
        logger.debug("Initialiazing a Mist WLAN")
        self.ssid = ssid
        self.site_id = site_id
        self.api = api
        if self._does_exist_on_cloud() == False:
            self.band = wlan_config['band'] if 'band' in wlan_config else None
            self.interface = wlan_config['interface'] if 'interface' in wlan_config else None
            self.hostname_ie = wlan_config['hostname_ie'] if 'hostname_ie' in wlan_config else None
            self.roam_mode = wlan_config['roam_mode'] if 'roam_mode' in wlan_config else None
            self.rateset = wlan_config['rateset'] if 'rateset' in wlan_config else None
            if 'auth' in wlan_config:
                if wlan_config['auth']['type'] == "psk":
                    self._validate_psk_configuration(wlan_config)
                elif wlan_config['auth']['type'] == "eap":
                    self._validate_dot1x_configuration(wlan_config)

    def _validate_psk_configuration(self, wlan_config: dict):
        """Validates the PSK configurations

        This method validates that the proper information if provided in the confi file related to PSK Authentication
        First if validates that the password is defined in the configuration file
        Then it validates that the password is not empty. If the password is empty, in the configuration file, it raises
        an exception.
        """
        try:
            self.auth = wlan_config['auth']
            if wlan_config['auth']['psk'] == "":
                logger.warning(
                    "Authentication Type: PSK\tWARNING:The password strength is not strong enough. Please use a longer and more complexe PSK.")
        except:
            raise Exception(
                "Authentication Type: PSK\tERROR:No password defined")

    def _validate_dot1x_configuration(self, wlan_config: dict):
        """Validates the 802.1X-EAP configurations

        This method validates that the proper information if provided in the confi file related to EAP Authentication
        If validates that Authentication Servers have been provided in the configuration file.
            If it is not the case, it raises an exception
        """
        try:
            if wlan_config['auth']['type'] == 'eap':
                if 'auth_servers' in wlan_config:
                    if not wlan_config['auth_servers']:
                        raise Exception(
                            "Authentication Type: EAP\tERROR: At least one RADIUS authentication server must be defined in your configuration file")
                    self.auth = wlan_config['auth']
                    self.auth_servers = wlan_config['auth_servers']
        except:
            raise Exception(
                "Authentication Type: EAP\tERROR: At least one RADIUS authentication server must be defined in your configuration file")

    def _does_exist_on_cloud(self) -> bool:
        """Validate if a WLAN profile already exists on the Mist cloud

        This function validates if a WLAN already on the Mist Cloud
        It sends the following GET API call to retreive all wlans part of an Site:
            GET https://api.mist.com/api/v1/sites/:site_id/wlans

        If the WLAN exists on the cloud, attributes are configured based on how the Wlan
        is configured on the cloud

        Returns:
            Bool: True if the wlans exists and False is it does not exist
        """
        wlans = self.api.get(f"sites/{self.site_id}/wlans")
        for wlan in wlans:
            if wlan['ssid'] == self.ssid:
                self.wlan_id = wlan['id']
                self.band = wlan['band']
                self.interface = wlan['interface']
                self.hostname_ie = wlan['hostname_ie']
                self.roam_mode = wlan['roam_mode'] if 'roam_mode' in wlan else None
                self.auth = wlan['auth']
                self.auth_servers = wlan['auth_servers'] if 'auth_servers' in wlan else None
                self.rateset = wlan['rateset'] if 'rateset' in wlan else None
                return True
        return False

    def create(self) -> dict:
        """Creates a new WLAN on the Mist Cloud

        This function create a new Mist WLAN within a Mist Site if the WLAN doesn't exists
        The following WLAN settings are configured:
            - ssid
            - band
            - interface
            - hostname_ie (enable or disable)
            - roam_mode (OKC, 11r, None)
            - auth (open, psk, eap)
            - auth_servers (if eap auth is used)
            - rateset (data rates)

        These values are being extracted from the configuration file.

        Returns:
            response_new_wlan: a Dict containing the content of the JSON POST reply sent by the Mist Cloud
        """
        logger.info(f"Creating WLAN:\t{self.ssid}")
        wlan_body = {}
        wlan_body['enabled'] = "true"
        wlan_body['ssid'] = self.ssid
        wlan_body['band'] = self.band if 'band' in self.__dict__ else None
        wlan_body['interface'] = self.interface if 'interface' in self.__dict__ else None
        wlan_body['hostname_ie'] = self.hostname_ie if 'hostname_ie' in self.__dict__ else None
        wlan_body['roam_mode'] = self.roam_mode if 'roam_mode' in self.__dict__ else None
        wlan_body['auth'] = self.auth if 'auth' in self.__dict__ else None
        wlan_body['auth_servers'] = self.auth_servers if 'auth_servers' in self.__dict__ else None
        wlan_body['rateset'] = self.rateset if 'rateset' in self.__dict__ else None

        if self._does_exist_on_cloud() == False:
            try:
                response_new_wlan = self.api.post(f"sites/{self.site_id}/wlans", wlan_body)
            except Exception:
                raise
            self.wlan_id = response_new_wlan['id']
            logger.info(f"WLAN created:\tNAME:{self.ssid}\tID:{self.wlan_id}")
            return response_new_wlan
        else:
            logger.info(f"WLAN already exists\tID:{self.wlan_id}")

    def delete(self) -> bool:
        """Delete a WLAN on the Mist Cloud

        Deletes a WLAN on the Mist cloud if the WLAN currently exisits. The function first checks
        if the WLAN currently exists on the Mist cloud or not.
        If the WLAN exists on the Mist cloud it send the following DELETE API call to delete the WLAN:
            DELETE https://api.mist.com/api/v1/sites/:site_id/wlans/:wlan_id

        Returns:
            bool: True if the WLAN is deleted successful, False if it is not deleted
        """
        logger.info(f"Deleting WLAN {self.ssid}")
        if self._does_exist_on_cloud():
            try:
                response_delete = self.api.delete(f"sites/{self.site_id}/wlans/{self.wlan_id}")
            except Exception:
                raise
            log = f"WLAN deleted\tID:{self.wlan_id}" if response_delete else f"WLAN not deleted\tID:{self.wlan_id}"
            logger.info(log)
            self.__delete__()
            return response_delete
        else:
            logger.error(f"WLAN was NOT deleted\tREASON: WLAN doesn't currently exist on Mist Cloud")
            return False

    def __delete__(self):
        """Deletes an instance of this WLAN class
        """
        logger.debug(f"Deleting Mist WLAN Instance\tNAME:{self.ssid}\tID:{self.wlan_id}")

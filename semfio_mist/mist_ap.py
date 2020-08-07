import json
from semfio_mist.logger import logger, logger_engine
from semfio_mist.config import Config
from semfio_mist.mist_api import API


class AP:
    """Mist AP Object

    This class is used to perform Mist AP operations. It is mainly used to initially configure
    Access Points as well as adjust their radio configurations.

    Attributes:
        mac: str defining the MAC address of the AP
        name: str defining the name of the AP
        site_id: str defining the ID of the site the AP belongs to
        api: API instance
        config: Config instance containing the content of the config file(s)
        id: str defining the ID of the Mist AP on the Mist Cloud once it has been claimed
        site_name: str defining the name of the site the AP belongs to
        model: str defining the model of the AP
        serial: str defining the serial number of the AP
        claim_code: str defining the claim code of the AP
        height: str defining the installation height of the AP
        orientation: str defining the orientation of an AP
        map: dict defining the map ID of the map the AP is placed on as well as the coordinates of its location
        radio_configs: dict defining both 2.4Ghz and 5Ghz radio configurations of the AP

    Methods:
        __init__(self, mac: str, site_id: str, api: API, config: Config, *args, **kwargs: dict):
            Used to initialize an AP instance and set some of the key Attributes
        _has_been_claimed(self, org_id) -> bool: Validate if an AP is already in an Organization inventory
        _does_belong_to_site(self) -> bool: Validate is an AP belongs to a site
        claim(self, org_id): Claim a Mist AP to an organization
        provision(self, ap_name): Assign an AP to a Mist Site
        configure_radios(self): Configure both 2.4GHz and 5GHz radio settings of a Mist AP
        unassign(self, org_id): Unassign an AP from a Mist Site. The AP will still be part of the Organization inventory
        release(self, org_id): Remove the AP from an Organization inventory
    """

    mac: str
    name: str
    site_id: str
    api: API
    config: Config
    id: str = None
    site_name: str = None
    model: str = None
    serial: str = None
    claim_code: str = None
    height: str = None
    orientation: str = None
    map: dict = {}
    radio_configs = {}

    def __init__(self, mac: str, site_id: str, api: API, config: Config, *args, **kwargs: dict):
        """Initializes a Mist AP instance

        Initialize the following object attributes:
            mac: a str defining the mac address of the AP using the value passed as an argument
            name: a str defining the name of the AP. It is retreived from the configuration file
            site_id: a str defining the site ID the AP belongs to using the value passed as an argument
            api: a API object that contains all the necessary methos to perform API calls
            config: a Config object containing the content of the config file(s)
            site_name: a str defining the name of the site the AP belongs to. It is retreived from the configuration file
            claim_code: a str used to claim an AP to a Mist organization. It is retreived from the configuration file
            height: a str used to defining the installation height of an AP. It is retreived from the configuration file
            orientation: a str used to define the orientation of an AP. It is retreived from the configuration file
            radio_configs: a dict containing the radio configurations. It is retreived from the configuration file

        Args:
            mac: MAC address of the AP
            site_id: Site ID of the site the AP belongs to, or Site ID of the site it will belong to
            api: API object that contains all the necessary methos to perform API calls
            config: a Config object containing the content of the config file(s)
        """
        logger.debug("Initialiazing a Mist AP")
        self.mac = mac
        self.name = config.data['ap']['name'] if 'name' in config.data['ap'] else None
        self.site_id = site_id
        self.api = api
        self.config = config
        self.site_name = config.data['site']['name']
        self.claim_code = config.data['ap']['claim_code'] if 'claim_code' in config.data['ap'] else None
        self.height = config.data['ap']['height'] if 'height' in config.data['ap'] else None
        self.orientation = config.data['ap']['orientation'] if 'orientation' in config.data['ap'] else None
        self.radio_configs['radio_config'] = {}

    def _has_been_claimed(self, org_id) -> bool:
        """Validates if an AP has already been claimed to an organization

        This functions validates if an AP has been claimed to an Organization by looking to see
        if it is part of the organization inventory.
        It sends the following GET API call to retreive the device inventory of the organization:
            GET https://api.mist.com/installer/orgs/:org_id/devices

        If the AP is part of this inventory (validation made against the MAC address of the AP),
        the function returns True. If not, it returns False.

        Returns:
            Bool: True if the AP has been claimed, False if not
        """
        logger.debug(
            f"Validating if AP {self.mac} has already been claim to Organization {org_id}")
        devices = self.api.get(f"installer/orgs/{org_id}/devices")
        for device in devices:
            if device['mac'] == self.mac:
                return True
        return False

    def _does_belong_to_site(self) -> bool:
        """Validates if an AP is part of a Mist site

        This function check if an AP is already assigned to a site based on
        the AP MAC Address

        It sends the following API Call to retrieve all the AP part of a site:
            GET https://api.mist.com/v1/sites/:site_id/devices

        If the AP is part of the site, this function set the following Attributes
        based on the API response content:
            id: str device id
            serial: str serial number of the AP
            model: str model name of the AP
            map['id']: str map ID if the AP is located on a map

        Returns:
            Bool: True if the AP is part of the site, False if it is not
        """
        logger.debug(f"Validating if a AP {self.mac} belongs to Site {self.site_id}")
        devices = self.api.get(f"sites/{self.site_id}/devices")
        for device in devices:
            if (device['type'] == "ap") and (device['mac'] == self.mac):
                self.id = device['id']
                self.serial = device['serial']
                self.model = device['model']
                self.map['id'] = device['map_id'] if 'map_id' in device else None
                return True
        return False

    def claim(self, org_id: str):
        """Claim an AP to an organization

        This function will claim an AP to an Organization. This is typically the first thing
        you would do taking the AP outside the box. The function checks if the AP has not
        been claimed yet first.

        The claim code of the AP is required for this operation. This claim code can be found
        at the back of the AP.

        It sends the following POST API Call to the Mist Cloud:
            POST https://api.mist.com/orgs/:org_id/inventory

        The claim code is sent as the POST request body in the following fashon:
            ["<claim_code>"]

        Once the AP has been claimed to the organization, the following attributes are configured:
            id: ID of the Mist AP object on the Mist cloud
            serial: serial number of the AP
            model: model of the AP

        Args:
            org_id: ID of the Organization
        """
        logger.debug(f"Claiming AP {self.mac} to Organization {org_id}")
        if self._has_been_claimed(self.api.org_id) == False:
            if self.claim_code != None:
                claim_body = []
                claim_body.append(f"{self.claim_code}")
                claim_response = self.api.post(f"orgs/{org_id}/inventory", claim_body)
                self.id = claim_response['inventory_added'][0]['id']
                self.serial = claim_response['inventory_added'][0]['serial']
                self.model = claim_response['inventory_added'][0]['model']
            else:
                raise Exception(f"No claim code has been provided to claim this AP.")

    def provision(self, ap_name: str):
        """Assign an AP to a Mist Site

        This functions assign a Mist AP to a Mist Site.
        It sends a PUT API Call to the Mist Cloud:
            PUT https://api.mist/com/installer/orgs/:org_id/devices/:ap_mac"

        The following data is configured:
            AP Name
            MAP ID (if the AP needs to be placed on a map)
            AP height (if this information is provided in the configuration files)
            AP orientation (if this information is provided in the configuration files)

        Once the AP is assigned to the site, the following attributes are updated:
            id: ID of the Mist AP object on the Mist cloud
            serial: serial number of the AP
            model: model of the AP

        Args:
            ap_name: name of the AP
        """
        logger.debug(f"Provisioning AP {self.mac}")
        ap_provision = {}
        ap_provision['name'] = ap_name
        ap_provision['site_id'] = self.site_id
        if (self.map) and ('id' in self.map):
            ap_provision['map_id'] = self.map['id']
        if self.height:
            ap_provision['height'] = self.height
        if self.orientation:
            ap_provision['orientation'] = self.orientation

        if self._does_belong_to_site() == False:
            try:
                response_provision = self.api.put(
                    f"installer/orgs/{self.api.org_id}/devices/{self.mac}", ap_provision)
            except Exception:
                raise
            self.id = response_provision['id']
            self.serial = response_provision['serial']
            self.model = response_provision['model']
        else:
            logger.info(f"AP already belongs to site\tID:{self.site_id}")

    def configure_radios(self):
        """Confiure Radio Settings of an AP

        This functions configure the configurations of both radios of an AP. Both of them
        are configured at the same time.

        It configures the following settings of the 2.4Ghz radio:
            Channel
            Tx Power

        It configures the following settings of the 5GHz radio:
            Channel
            Channel Bandwidth
            Tx Power

        It sends a PUT API Call to the Mist Cloud:
            PUT https://api.mist.com/sites/:site_id/devices/:device_id
        """
        logger.debug(f"Configuring AP Radio Settings")
        if self._does_belong_to_site():
            self.radio_configs['radio_config']['band_24'] = {}
            self.radio_configs['radio_config']['band_24']['power'] = self.config.data['ap']['24']['power']
            self.radio_configs['radio_config']['band_24']['channel'] = self.config.data['ap']['24']['channel']
            self.radio_configs['radio_config']['band_5'] = {}
            self.radio_configs['radio_config']['band_5']['power'] = self.config.data['ap']['5']['power']
            self.radio_configs['radio_config']['band_5']['bandwidth'] = self.config.data['ap']['5']['bandwidth']
            self.radio_configs['radio_config']['band_5']['channel'] = self.config.data['ap']['5']['channel']
            radio_configs_response = self.api.put(
                f"sites/{self.site_id}/devices/{self.id}", self.radio_configs)
            logger.info(f"AP: {self.name}\t2.4GHz Radio Configured:\
                        CHANNEL:{radio_configs_response['radio_config']['band_24']['channel']}\
                        POWER:{radio_configs_response['radio_config']['band_24']['channel']}")
            logger.info(f"AP: {self.name}\t5GHz Radio Configured:\
                        CHANNEL:{radio_configs_response['radio_config']['band_5']['channel']}\
                        BANDWIDTH:{radio_configs_response['radio_config']['band_5']['bandwidth']}\
                        POWER:{radio_configs_response['radio_config']['band_5']['power']}")
        else:
            raise Exception(f"AP {self.name} does not belong to a site.")

    def unassign(self, org_id: str):
        """Unassign an AP from any site

        This function unassign an AP from a site. The AP stays in the inventory of the Organization
        and can be assign to other sites.

        It sends a PUT API Call to the Mist cloud:
            PUT https://api.mist.com/orgs/:org_id/inventory

        The body of the PUT API call is organized as follow:
            {
                "op": "unassign",
                "macs": [
                    "<ap_mac_address>"
                ]
            }

        Once the call is made, the site_id attribute and site_names are updated to None
        """
        logger.debug(f"Unassigning AP {self.mac} from site {self.site_id}")
        if self._does_belong_to_site():
            unassign_body = {}
            unassign_body['op'] = "unassign"
            unassign_body['macs'] = []
            unassign_body['macs'].append(f"{self.mac}")
            unassign_response = self.api.put(f"orgs/{org_id}/inventory", unassign_body)
            logger.debug(unassign_response)
            if unassign_response['success'][0] == self.mac:
                logger.info(f"AP {self.mac} has been unassigned from site {self.site_id}")
                self.site_id = None
                self.site_name = None
            else:
                logger.error(f"AP has not been unassigned from site")

    def release(self, org_id: str):
        """Release an AP from any site

        This function deletes an AP from an organization inventory. It first checks if
        the AP is part of the inventory.

        It sends a PUT API Call to the Mist Cloud:
            PUT https://api.mist.com/orgs/:org_id/inventory

        The body of the PUT API call is organized as follow:
            {
                "op": "delete",
                "macs": [
                    "<ap_mac_address>"
                ]
            }

        Once the call is made, the site_id attribute and site_names are updated to None
        """
        logger.debug(f"Realising AP {self.mac} from organization {org_id}")
        if self._has_been_claimed(org_id):
            release_body = {}
            release_body['op'] = "delete"
            release_body['macs'] = []
            release_body['macs'].append(f"{self.mac}")
            release_response = self.api.put(f"orgs/{org_id}/inventory", release_body)
            logger.debug(release_response)
            if release_response['success'][0] == self.mac:
                logger.info(f"AP {self.mac} has been released from organization {org_id}")
                self.site_id = None
                self.site_name = None
            else:
                logger.error(f"AP has not been released from organization")
        else:
            logger.info(f"AP {self.mac} is currently not part of organization {org_id}")

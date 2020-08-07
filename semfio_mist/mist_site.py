from semfio_mist.logger import logger, logger_engine
from semfio_mist.config import Config
from semfio_mist.mist_api import API


class Site:
    """Mist Site Object
    """

    site_id: str = None
    name: str
    api: API
    org_id: str
    timezone: str = None
    country_code: str = None
    rftemplate_id: str = None
    secpolicy_id: str = None
    alarmtemplate_id: str = None
    lat: float = None
    lng: float = None
    sitegroup_ids: [str] = None
    address: str = None

    def __init__(self, name: str, api: API, config: Config, site_id: str = None, *args, **kwargs):
        """Initializes the Mist Site instance

        Initialize the following object attributes:
            name: a str defining the name of the site (Note: this class does not allow to have
                    2 sites with the same name)
            org_id: a str defining the organization ID (coming from the API Class)
            api: a API object that contains all the necessary methos to perform API calls
            config: a Config object containing the content of the config file
            site_id: a str defining the site ID (for future use)

        This function validates if the site already exists on the Mist Cloud based on its name
        If it does, the local attributes are configued via the _does_exist_on_cloud method.
        If it does not, this function configures the attributes using the data of the config file
        """
        logger.debug("Initialiazing a Mist Site")
        self.name = name
        self.org_id = api.org_id
        self.api = api
        if self._does_exist_on_cloud() == False:
            self.timezone = config.data['site']['timezone'] if 'timezone' in config.data['site'] else None
            self.country_code = config.data['site']['country_code'] if 'country_code' in config.data['site'] else None
            self.address = config.data['site']['address'] if 'address' in config.data['site'] else None
            self.lat = config.data['site']['lat'] if 'lat' in config.data['site'] else None
            self.lng = config.data['site']['lng'] if 'lng' in config.data['site'] else None

    def _does_exist_on_cloud(self) -> bool:
        """Validate if a site already exists on the Mist cloud

        This function validates if a site already on the Mist Cloud
        It sends the following GET API call to retreive all sites part of an Organization:
            GET https://api.mist.com/api/v1/orgs/:org_id

        If the site exists on the cloud, this functions uses the JSON coming from the Mist Cloud
        to configure the following instance's attributes based on the current configuration of the site:
            - Site ID
            - Timezone
            - Country code
            - Address
            - Latitude
            - Longitude

        Returns:
            Bool: True if the site exists and Fals is it does not exist
        """
        sites = self.api.get(f"orgs/{self.org_id}/sites")
        for site in sites:
            if site['name'] == self.name:
                self.site_id = site['id']
                self.timezone = site['timezone'] if 'timezone' in site else None
                self.country_code = site['country_code'] if 'country_code' in site else None
                self.address = site['address'] if 'address' in site else None
                self.lat = site['latlng']['lat'] if 'latlng' in site else None
                self.lng = site['latlng']['lng'] if 'latlng' in site else None
                return True
        return False

    def create(self) -> dict:
        """Creates a new site on the Mist Cloud

        This function create a new Mist Site within a Mist Organization if the site doesn't exists
        The following site settings are configured:
            - name
            - timezone
            - country code
            - address
            - Latitude
            - Longitude

        These values are being extracted from the configuration file.

        Returns:
            response_new_site: a Dict containing the content of the JSON POST reply sent by the Mist Cloud

        """
        logger.info(f"Creating site:\t{self.name}")
        site_body = {}
        site_body['name'] = self.name
        if 'timezone' in self.__dict__:
            site_body['timezone'] = self.timezone
        if 'country_code' in self.__dict__:
            site_body['country_code'] = self.country_code
        if 'address' in self.__dict__:
            site_body['address'] = self.address
        if 'lat' in self.__dict__ and 'lng' in self.__dict__:
            site_body['latlng'] = {'lat': self.lat, 'lng': self.lng}

        if self._does_exist_on_cloud() == False:
            try:
                response_new_site = self.api.post(f"orgs/{self.org_id}/sites", site_body)
            except Exception:
                raise
            self.site_id = response_new_site['id']
            logger.info(f"Site created:\tNAME:{self.name}\tID:{self.site_id}")
            return response_new_site
        else:
            logger.info(f"Site already exists\tID:{self.site_id}")

    def configure_persist_config_on_device(self, config_persistence_enable: bool) -> dict:
        """Configure the AP Config Persistence feature

        Updates the configurations of a site to enable the following feature:
            AP Config Persistence (or 'persist_config_on_device')

        Args:
            config_persistence_enable: bool defining to either enable or disable the feature

        Returns:
            response_configure: a Dict containing the content of the JSON PUT reply sent by the Mist Cloud
        """
        logger.debug(f"Configuring AP Config Persitence for this site: {self.name}")
        data_put = {}
        data_put['persist_config_on_device'] = config_persistence_enable
        try:
            response_configure = self.api.put(f"sites/{self.site_id}/setting", data_put)
        except Exception:
            raise
        self.config_persistence_enable = config_persistence_enable
        logger.info(f"AP Config Persistence configured\tSITE:{self.name}")
        return response_configure

    def delete(self) -> bool:
        """Delete a site on the Mist Cloud

        Deletes a Site on the Mist cloud if the site currently exisits. The function first checks
        if the site currently exists on the Mist cloud or not.
        If the site exists on the Mist cloud it send the following DELETE API call to delete the site:
            DELETE https://api.mist.com/api/v1/sites/:site_id

        Returns:
            bool: True if the site is deleted successful, False if it is not deleted
        """
        logger.info(f"Deleting site {self.site_id}")
        if self._does_exist_on_cloud():
            try:
                response_delete = self.api.delete(f"sites/{self.site_id}")
            except Exception:
                raise
            log = f"Site deleted\tID:{self.site_id}" if response_delete else f"Site not deleted\tID:{self.site_id}"
            logger.info(log)
            self.__delete__()
            return response_delete
        else:
            logger.error(f"Site was NOT deleted\tREASON: Site doesn't currently exist on Mist Cloud")
            return False

    def __delete__(self):
        """Deletes an instance of this Site class
        """
        logger.debug(f"Deleting Mist Site Instance\tNAME:{self.name}\tID:{self.site_id}")

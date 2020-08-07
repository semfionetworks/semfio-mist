import requests
import os
import json
from semfio_mist.config import Config
from semfio_mist.logger import logger


class Token:
    """Mist Token Object

    This class allows us to manage and handle the token(s) used to make calls to the
    Mist API cloud.

    It assumes that the your MIST API MASTER TOKEN is store in an environment variable
    on your system.

    * MACOS
    To create an environmental variable on macOS, run this command:
        export MIST_TOKEN='<your-token-here>'

    Note that this variable will be lost when you close the terminal. In order to create
    an environment variable that will be saved, open the following file:
        > vi ~/.zshrc
            > add the following line: export MIST_TOKEN='<your-token-here>'
                > save the .zshrc file
                    > run this command: source ~/.zshrc

    In order to validate that the variable is defined, run this command:
        export | grep MIST_TOKEN


    * WINDOWS
    To create the user env var, use the following command from a command window on a
    Windows 10 machine:
        setx MIST_TOKEN "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    To verify the env var has been correctly created, open a new command windows and
    type the following command to verify that the env var is now gloablly available to
    the user account being used:
        echo %MIST_TOKEN%

    Note that the env var is only available in a NEW command window. The env var is
    now permanently avaialble to all processes running under the current user account.
    The env var will not be available to other users on the same machine.

    To remove the env var value, set the env var with a blank value in a command window
    (the env var will still exist, but will have no value):
        setx MIST_TOKEN ""

    Or, alternatively it may be deleted via the Windows 10 GUI environmental variable
    editing tool:
        > Start
            > Control Panel
                > System & Security
                    > System
                        > Advanced System Settings
                            > Environmental Variables (User section)

    This Class gives use the ability to create a temporary token that could be used to perform
    all API calls required by a specific script or program.

    The MASTER TOKEN will only be used to create and delete the temporary token.

    Attributes:
        MASTER_TOKEN: str for the KEY main Mist API Token
        tmp_token_id: str for the ID of the temporary token
        tmp_token_key: str for the KEY of the temporary token
    """

    def __init__(self, config: Config):
        """Initialized the Mist Token object

        Set the MASTER_TOKEN variable:
            - Retrieve the environment variable called MIST_TOKEN
            - Make sure the this environ is set on your system
                - Run this command on MacOS: export MIST_TOKEN='<your-token-here>'
        """
        try:
            self.MASTER_TOKEN = os.environ['MIST_TOKEN'] if 'MIST_TOKEN' in os.environ else config.data['token']
        except Exception:
            raise

    def get_tmp_token(self, session: requests.Session):
        """Creates a Mist token 'on the fly' to be used witin a specific script.

        The following API call is made to the Mist Cloud to create a new token:
            POST https://api.mist.com/api/v1/self/apitokens

        Set the following class variables:
         - tmp_token_key: temporary token KEY received from Mist Cloud after creation
         - tmp_token_id: temporary token ID received from Mist Cloud after creation
        """
        api_url = "https://api.mist.com/api/v1/self/apitokens"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Token {self.MASTER_TOKEN}"}
        try:
            response = session.post(api_url, data={}, headers=headers)
            if response.status_code == 200:
                token = json.loads(response.text)
                self.tmp_token_key = token['key']
                self.tmp_token_id = token['id']
                logger.debug(
                    f"Temporary Token created: {self.tmp_token_key}\tID: {self.tmp_token_id}")
            else:
                raise ValueError(
                    f"Error connecting to Mist API!\tRESPONSE:'{response.status_code} - {response.text}'")
        except Exception:
            raise

    def delete_tmp_token(self, session: requests.Session):
        """Deletes the temporary token

        Deletes the temporary Mist Token stored in self.tmp_token_key
        using its ID stored in self.tmp_token_id

        The following API call is made to the Mist Cloud to delete the token:
            DELETE https://api.mist.com/api/v1/self/apitokens/:token_id
        """
        if "tmp_token_id" in self.__dict__:
            api_url = f"https://api.mist.com/api/v1/self/apitokens/{self.tmp_token_id}"
            headers = {"Content-Type": "application/json",
                       "Authorization": f"Token {self.MASTER_TOKEN}"}
            try:
                response = session.delete(api_url, headers=headers)
                if response.status_code == 200:
                    logger.debug(f"Token deleted\tID: {self.tmp_token_id}")
                else:
                    raise ValueError(
                        f"Error connecting to Mist API!\tRESPONSE:'{response.status_code} - {response.text}'")
            except Exception:
                raise
        else:
            raise ValueError(f"tmp_token_id does not exits.")


class API:
    """ Mist API Object

    Enables us to perform API calls to the Mist cloud

    Attributes:
        session: requests.Session object used to open a TCP connection for multiple API calls
        mist_cloud_url: str use to define the URL of the Mist cloud used for the API calls
        org_id: str ID of the Mist organization used within the API calls
        _mist_token: Token object containing the token used for the API calls
        _headers: dict containing the header used for the API calls

    """

    mist_cloud_url = "https://api.mist.com/api/v1/"
    session: requests.Session
    org_id: str
    _mist_token: Token
    _headers: dict = {}

    def __init__(self, config: Config, cloud: str = "", *args, **kwargs):
        """Initialized the Mist API object.

        Initialize the following object attributes:
            session: a new request.session is created and store in this attribute
            mist_cloud_url: if the cloud arg is set to EU, this attribute is adjusted accordingly
            _mist_token: a new Token object is created and a temporary token is requested to be used by this program
            org_id: retreived from MIST_ORG environement variable if exists or from the JSON config file otherwise
            _headers: dict containing the temporary token for authorization

        At the end of this Initialization, we have all the elements ready to make API calls
        towards the Mist cloud.

        Args:
            config: Config object containing the content of the config file
            cloud: str (Optional), "" to use US Mist cloud, "EU" to use European Mist Cloud
        """
        logger.debug("Initialiazing connection to the Mist API")
        self.session = requests.Session()
        self._mist_token = Token(config)
        self._mist_token.get_tmp_token(self.session)
        self.org_id = os.environ['MIST_ORG'] if 'MIST_ORG' in os.environ else config.data['org_id']
        self._headers = {"Content-Type": "application/json",
                         "Authorization": f"Token {self._mist_token.tmp_token_key}"}
        if cloud == "EU":
            self.mist_cloud_url = "https://api.eu.mist.com/api/v1/"

    def _verify_response(self, response: requests.Response) -> dict:
        """Verify the Status of the API GET or POST call

        If the API call was successful, it converts the JSON reply into a python dictionary
        If the API call was unsucessful, it logs an error message with the details

        Returns:
            reponse_text: a Dict containing the content of the JSON reply sent by Mist Cloud
        """
        response_text = json.loads(response.text)
        logger.debug(f"API CAL Status Code: {response.status_code}")
        if response.status_code >= 400:
            logger.error(
                f"API Call error {response.status_code}: {response_text}")
        else:
            return response_text

    def _verify_delete_response(self, response: requests.Response) -> bool:
        """Verify the status of a DELETE API Call

        If the API call was successful, it returns True
        If the API call was unsucessful, it logs an error and returns False

        Returns:
            Bool: stating the status of the DELETE API CALL
        """
        response_text = json.loads(response.text)
        logger.debug(f"API CALL Status Code: {response.status_code}")
        if response.status_code != 200:
            logger.error(
                f"API Call error {response.status_code}: {response_text['message']}")
            return False
        else:
            return True

    def get(self, call_url: str) -> dict:
        """Performs a GET API call to the Mist cloud

        Args:
            call_url: str defining the second part of the API api_url
                Example: "org/:org_id/sites" in "https://api.mist.com/api/v1/org/:org_id/sites"

        Returns:
            A dict containing the content of the response
        """
        call_url = self.mist_cloud_url + call_url
        try:
            logger.debug(f"Sending API GET CALL: {call_url}")
            response = self.session.get(call_url, headers=self._headers)
        except Exception:
            raise
        return self._verify_response(response)

    def post(self, call_url: str, body: dict) -> dict:
        """Performs a POST API call to the Mist cloud

        Args:
            call_url: str defining the second part of the API api_url
                Example: "org/:org_id/sites" in "https://api.mist.com/api/v1/org/:org_id/sites"
            body: dict containing the data to be sent along with the POST API Call

        Returns:
            A dict containing the content of the response
        """
        call_url = self.mist_cloud_url + call_url
        try:
            logger.debug(f"Sending API POST CALL: {call_url}")
            response = self.session.post(call_url, data=json.dumps(body), headers=self._headers)
        except Exception:
            raise
        return self._verify_response(response)

    def put(self, call_url: str, body: dict) -> dict:
        """Performs a PUT API call to the Mist cloud

        Args:
            call_url: str defining the second part of the API api_url
                Example: "org/:org_id/sites" in "https://api.mist.com/api/v1/org/:org_id/sites"
            body: dict containing the data to be sent along with the PUT API Call

        Returns:
            A dict containing the content of the response
        """
        call_url = self.mist_cloud_url + call_url
        try:
            logger.debug(f"Sending API PUT CALL: {call_url}")
            response = self.session.put(call_url, data=json.dumps(body), headers=self._headers)
        except Exception:
            raise
        return self._verify_response(response)

    def delete(self, call_url: str) -> bool:
        """Performs a DELETE API call to the Mist Cloud

        Args:
            call_url: str defining the second part of the API api_url
                Example: "org/:org_id/sites" in "https://api.mist.com/api/v1/org/:org_id/sites"

        Returns:
            Bool: indicating if the element was deleted
        """
        call_url = self.mist_cloud_url + call_url
        try:
            logger.debug(f"Sending API DELETE CALL: {call_url}")
            response = self.session.delete(call_url, headers=self._headers)
        except Exception:
            raise
        return self._verify_delete_response(response)

    def __exit__(self):
        self._mist_token.delete_tmp_token(self.session)
        self.session.close()
        logger.debug("Connection to the Mist API closed")

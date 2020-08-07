import json
from semfio_mist.logger import logger


class Config:
    """Config Object

    User configuration information will be loaded into this Object
    Make sure that all the desired data is added to a JSON configuration file
    before running the script.

    Attributes:
        filename: str script configuration filename wirtten in JSON
        data: A dict containing the content of the filename
    """

    def __init__(self, filename, *args, **kwargs):
        """Inits Config class

        Loads the content of the JSON configuration file into the data attribute (dict)

        Args:
            filename: JSON configuration file
        """
        self.filename = filename

        try:
            with open(self.filename) as config_file:
                file_content = config_file.read()
        except Exception as e:
            logger.error(f"Unable to open the following configuration file: {filename}")
            raise e

        self.data = json.loads(file_content)

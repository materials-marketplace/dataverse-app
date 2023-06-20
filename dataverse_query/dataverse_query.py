"""Query dataverse via its API."""
from typing import Dict
from urllib.parse import urljoin

import requests
from requests.exceptions import HTTPError

from dataverse_query.utils import convert_to_global_search_response


class DataverseQuery:
    """Class used for querying the dataverse through its API."""

    def __init__(self, repo_url: str):
        self.base_url = urljoin(repo_url, "api/")

    def _execute_query(self, url: str, payload: Dict[str, str]) -> requests.Response:
        """Execute a query given the payload on the pre-defined url.

        Args:
            url (str): url where the query will be done
            payload (Dict[str, str]): Parameters for the query

        Raises:
            HTTPError: If the query is not valid

        Returns:
            Response: Response to the query
        """
        r = requests.get(url, params=payload, verify=False)
        r.raise_for_status()
        return r

    def search_dataset(self, query: str):
        url = urljoin(self.base_url, "search/")
        return self._execute_query(url, {"q": query})

    def get_dataset(self, dataset_id: str) -> Dict[str, str]:
        """Get the information of a dataset given its ID.

        Args:
            dataset_id (str): unique identifier of a dataset

        Returns:
            Dict[str, str]: JSON information of a dataset
        """
        url = urljoin(self.base_url, "access/dataset/:persistentId/")
        response = self._execute_query(
            url, {"persistentId": dataset_id, "download_name": "test_download.zip"}
        )
        return response.content

    def get_dataset_metadata(self, dataset_id: str) -> Dict[str, str]:
        """Get the information of a dataset given its ID.

        Args:
            dataset_id (str): unique identifier of a dataset

        Returns:
            Dict[str, str]: JSON information of a dataset
        """
        url = urljoin(self.base_url, "datasets/:persistentId/")
        json_payload = self._execute_query(url, {"persistentId": dataset_id}).json()
        return json_payload["data"]

    def get_all_datasets(self) -> Dict[str, str]:
        """Get all the datasets hosted.

        Returns:
            Dict[str, str]: [description]
        """
        url = urljoin(self.base_url, "search/")
        return self._execute_query(url, {"q": "*", "type": "dataset"}).json()

    def global_search(self, query: str) -> Dict[str, str]:
        """global search on dataverse
        execute the search query on the dataverse

        Args:
            query (str): search query to execute

        Returns:
            Dict[str, str]: response compatible with global search datasource response

        """
        url = urljoin(self.base_url, "search/")
        json_payload = self._execute_query(url, {"q": query}).json()
        response = convert_to_global_search_response(json_payload, self.base_url)
        return response

from typing import Dict


def convert_to_global_search_response(
    response: Dict[str, str], baseUrl: str
) -> Dict[str, str]:
    """Convert the dataverse response to be compatible with global search's expectation

    Args:
        response (Dict[str, str]): JSON response from dataverse search
        baseUrl (str): base url

    Returns:
        Dict[str, str]:response compatible with global search datasource response
    """

    def _get_link(dataverse_instance: Dict[str, str], baseUrl: str) -> str:
        """Generate the link of the dataverse/ dataset/ file dataverse_instance from persistent id.

        Args:
            dataverse_instance (Dict[str, str]): Dictionary for details
            baseUrl (str): base url
        Returns:
            str: url string corresponding to the datasource
        """
        # remove api/ from the end of the url
        baseUrl = baseUrl[:-4]
        type_of_datasource = dataverse_instance.get("type")
        if type_of_datasource == "dataverse":
            return dataverse_instance.get("url")
        elif type_of_datasource == "dataset":
            persistent_id = dataverse_instance.get("global_id")
        elif type_of_datasource == "file":
            persistent_id = dataverse_instance.get("file_persistent_id")
        else:
            return ""
        return f"{baseUrl}{type_of_datasource}.xhtml?persistentId={persistent_id}"

    data = response["data"]["items"]
    datasource = [
        dict(
            {
                "label": dataverse_instance.get("name"),
                "description": dataverse_instance.get("description"),
                "link": _get_link(dataverse_instance, baseUrl),
            }
        )
        for dataverse_instance in data
    ]

    return datasource

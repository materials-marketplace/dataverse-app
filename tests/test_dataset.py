"""Tests the functionality of the Dataset class."""

from unittest import TestCase, main

from dataverse_query.dataset import JSON, Dataset
from dataverse_query.dataverse_query import DataverseQuery


class DatasetTest(TestCase):
    """Tests the functionality of the Dataset class."""

    response: JSON
    dataset: Dataset

    @classmethod
    def setUpClass(cls) -> None:
        """Create a query and execute it to get a sample dataset."""
        dq = DataverseQuery("https://entrepot.recherche.data.gouv.fr")
        cls.response = dq.get_dataset("doi:10.15454/DOWA7X")

    def setUp(self) -> None:
        """For each test, save the sample dataset the `self.dataset`."""
        self.dataset = Dataset(self.response)

    def test_create_DCAT(self) -> None:
        """Check the correctness of the DCAT conversion function output."""
        self.dataset.to_dcat()  # For now just test that it works.


if __name__ == "__main__":
    main()

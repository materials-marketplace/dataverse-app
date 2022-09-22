# Dataverse App for MarketPlace
This app will connect to a [dataverse](https://dataverse.org/) instance (url defined in `app.py`), and allow to get all the datasets, individual ones, or just their metadata.
It also implements the `globalSearch` capability to integrate with the platform service.

Datasets are currently (partially) mapped to a DCAT representation, and exported as a `ttl` file.

## Authors
    - Pranjali Singh (pranjali.singh@iwm.fraunhofer.de)
    - Pablo de Andres (pablo.de.andres@iwm.fraunhofer.de)
    - José Manuel Domínguez (jose.manuel.dominguez@iwm.fraunhofer.de)

## Deployment
An instance of this app can be deployed by running on this root folder:
```sh
docker compose up
```
Remember to use the `-d` option to start the containers in the background

from shark_metadata.delivery_data import DeliveryData


def test_metadata_has_expected_fields():
    given_delivery_note_data = {"DTYPE": "Phytoplankton", "ORDERER": "HAV"}

    # Given a delivery data object
    delivery_data = DeliveryData(delivery_note=given_delivery_note_data)

    # When looking at all available fields
    metadata = delivery_data.generate_metadata()

    # Then they correspond to the expected fields
    orderered_expected_fields = (
        "datatype",
        "monitoring_program",
        "dataset_filename",
        "keywords",
        "method_description",
        "measuring_area_type",
        "coordinate_system",
        "platform_class",
        "license",
        "min_year",
        "max_year",
        "min_date",
        "max_date",
        "min_longitude_dd",
        "max_longitude_dd",
        "min_latitude_dd",
        "max_latitude_dd",
        "stations",
        "parameters",
        "taxonomic_coverage",
        "originator",
        "orderer",
        "data_holding_centre",
        "database_reference",
        "internet_access",
        "citation",
    )

    assert set(metadata.keys()) == set(orderered_expected_fields)

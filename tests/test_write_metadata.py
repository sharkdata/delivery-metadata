from delivery_metadata import DeliveryMetadata


def test_metadata_has_expected_fields():
    # Given a metadata object
    metadata = DeliveryMetadata()

    # When looking at all available fields
    metadata_fields = metadata.fields

    # Then they correspond to the expected fields
    orderered_expected_fields = (
        "datatype",
        "abstract",
        "description",
        "dataset_filename",
        "discipline",
        "measuring_area_type",
        "coordinate_system",
        "platform_class",
        "access_constraints",
        "min_year",
        "max_year",
        "min_date",
        "max_date",
        "min_longitude_dd",
        "max_longitude_dd",
        "min_latitude_dd",
        "max_latitude_dd",
        "taxonomic_coverage",
        "originator",
        "contact",
        "orderer",
        "data_holding_centre",
        "data distributor",
        "database_reference",
        "internet_access",
        "address",
        "postal_code",
        "city",
        "phone",
        "email",
        "citation",
    )

    assert metadata_fields == orderered_expected_fields

import polars as pl

from shark_metadata.delivery_data import DeliveryData


def test_metadata_has_expected_fields(mock_nodccode_get_config_path):
    data = pl.DataFrame(
        {
            "dataset_name": ["test"] * 2,
            "version": ["123"] * 2,
            "delivery_datatype": ["Phytoplankton"] * 2,
            "monitoring_program_code": ["001"] * 2,
            "reporting_institute_name_en": ["test"] * 2,
            "sample_orderer_name_en": ["test"] * 2,
            "sample_project_name_en": ["test"] * 2,
            "scientific_name": ["test"] * 2,
        }
    )

    # Given a delivery data object
    delivery_data = DeliveryData(data)

    # When looking at all available fields
    metadata = delivery_data.generate_metadata()

    # Then they correspond to the expected fields
    orderered_expected_fields = (
        "citation",
        "coordinate_system",
        "data_holding_centre",
        "database_reference",
        "dataset_filename",
        "datatype",
        "gcmd_science_keywords",
        "internet_access",
        "license",
        "max_date",
        "max_latitude_dd",
        "max_longitude_dd",
        "max_year",
        "measuring_area_type",
        "method_description",
        "min_date",
        "min_latitude_dd",
        "min_longitude_dd",
        "min_year",
        "monitoring_program",
        "orderer",
        "originator",
        "parameters",
        "platform_class",
        "stations",
        "taxonomic_coverage",
        "version",
    )

    assert set(metadata.keys()) == set(orderered_expected_fields)

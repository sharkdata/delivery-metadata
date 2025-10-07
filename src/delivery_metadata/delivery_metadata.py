class DeliveryMetadata:
    _fields = (
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

    @property
    def fields(self):
        return self._fields

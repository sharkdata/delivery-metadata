class SharkMetadataError(Exception):
    pass


class MissingFileError(SharkMetadataError):
    pass


class MissingMetadataError(SharkMetadataError):
    pass

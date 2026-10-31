from enum import Enum


class ResponseMessage(Enum):
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    FILE_NOT_FOUND = "file_not_found"

    INDEXING_SUCCESS = "indexing_success"
    FILE_DELETED = "file_deleted"

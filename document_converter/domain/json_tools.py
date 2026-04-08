from typing import Any, List, Tuple


class JsonValidationError(ValueError):
    def __init__(
        self,
        *,
        code: str,
        source_name: str,
        index: int | None = None,
    ):
        self.code = code
        self.source_name = source_name
        self.index = index
        super().__init__(f"{code}:{source_name}:{index}")


def extract_json_records_and_keys(
    json_data: Any,
    *,
    source_name: str,
) -> Tuple[List[dict], Tuple[str, ...]]:
    if isinstance(json_data, dict):
        records = [json_data]
    elif isinstance(json_data, list):
        if not json_data:
            raise JsonValidationError(
                code="empty_array",
                source_name=source_name,
            )
        if not all(isinstance(item, dict) for item in json_data):
            raise JsonValidationError(
                code="non_object_item",
                source_name=source_name,
            )
        records = json_data
    else:
        raise JsonValidationError(
            code="invalid_root_type",
            source_name=source_name,
        )

    keys = tuple(sorted(records[0].keys()))
    expected = set(keys)
    for index, record in enumerate(records, start=1):
        record_keys = set(record.keys())
        if record_keys != expected:
            raise JsonValidationError(
                code="inconsistent_item_keys",
                source_name=source_name,
                index=index,
            )

    return records, keys

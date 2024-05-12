import json


class ResponsePayloadOption:
    def __init__(self, id: int, name: str, is_multi: bool, is_required: bool):
        self.id = id
        self.name = name
        self.is_multi = is_multi
        self.is_required = is_required

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "isMulti": self.is_multi,
                "isRequired": self.is_required,
            },
            ensure_ascii=False,
        )

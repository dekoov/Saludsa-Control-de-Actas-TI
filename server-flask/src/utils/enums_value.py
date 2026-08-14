from enum import Enum

from sqlalchemy import Enum as SAEnum


def value_enum(enum_class: type[Enum]) -> SAEnum:
    return SAEnum(
        enum_class,
        values_callable=lambda enum_cls: [
            member.value for member in enum_cls
        ],
    )

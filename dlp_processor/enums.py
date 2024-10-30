from enum import Enum


class SourceType(str, Enum):
    FILE = "file"
    MESSAGE = "message"

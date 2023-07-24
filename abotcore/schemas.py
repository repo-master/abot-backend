from enum import Enum


class ChatServiceType(str, Enum):
    DUMMY = "dummy"
    RASA = "rasa"
    LANGCHAIN_GENESIS = "genesis"
    LANGCHAIN_FUNCTION = "genesis_fn"


from rasa.core.channels import InputChannel

from abc import ABC, abstractmethod


class CustomInputChannel(ABC, InputChannel):
    '''A custom iput channel class that has some extra methods'''
    @abstractmethod
    async def init_agent(self, agent):
        pass

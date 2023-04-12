
import asyncio
from aiogram import Bot, Dispatcher, types as aiogtypes

from .customchannel import CustomInputChannel
from rasa.core.channels import OutputChannel, UserMessage

from rasa.core.agent import Agent

from typing import Optional


class TelegramOutput(OutputChannel):
  def __init__(self, dp: Dispatcher):
    self.dp = dp

  async def send_text_message(self, recipient_id: str, text: str, **kwargs) -> None:
    """Sends text message."""
    for message_part in text.strip().split("\n\n"):
      await self.dp.bot.send_message(recipient_id, message_part)

  async def send_image_url(self, recipient_id: str, image: str, **kwargs) -> None:
    """Sends an image."""
    await self.dp.bot.send_photo(recipient_id, image)


class TelegramInput(CustomInputChannel):
  @classmethod
  def name(cls):
    return "telegram_bot"

  @classmethod
  def from_credentials(cls, credentials):
    if not credentials:
      cls.raise_missing_credentials_exception()

    return cls(
        credentials.get("access_token")
    )

  def __init__(self, access_token, debug_mode: bool = True):
    self.access_token = access_token
    self.bot = Bot(self.access_token)
    self._outchannel = None

  async def init_agent(self, agent):
    self.dp = Dispatcher(self.bot, loop=asyncio.get_event_loop())
    self._outchannel = TelegramOutput(self.dp)
    await self._init_dp_handlers(agent)
    self._poll_task = asyncio.create_task(self.dp.start_polling())

  async def _init_dp_handlers(self, agent: Agent):
    @self.dp.message_handler()
    async def handler(message : aiogtypes.Message):
      user_msg = UserMessage(
        text=message.text,
        output_channel=self._outchannel,
        sender_id=str(message.from_id),
        message_id=message.message_id,
        metadata={'content_type': message.content_type}
      )
      await message.answer_chat_action("typing")
      await agent.handle_message(user_msg)

  def get_output_channel(self) -> Optional["OutputChannel"]:
    return self._outchannel

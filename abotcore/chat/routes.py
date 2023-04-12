
from fastapi import APIRouter

from .schemas import ChatMessageIn, ChatMessageOut
from abotcore.mlmodels.rasa_agent import handle_message

from rasa.core.channels import UserMessage

from typing import Optional, List


# Endpoint router
router = APIRouter(prefix='/chat')

# Default route (/chat)
@router.post("")
async def chat(msg: ChatMessageIn) -> Optional[List[ChatMessageOut]]:
  '''Get the Rasa model's response to the user's message'''

  user_message = UserMessage(**msg.dict())

  # vvv show typing dots here

  # Generate responses from the Rasa Agent, wait for all replies and send back as JSON.
  # sender_id is optional in this case
  responses : Optional[List[ChatMessageOut]] = await handle_message(user_message)

  # ^^^ hide typing dots here

  # Send back all generated responses at once
  return responses

# Used as a heartbeat and general status enquiry (/chat/status)
@router.get("/status")
def status():
  return ""

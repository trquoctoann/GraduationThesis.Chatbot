import os
from typing import Final

from discord import Client, Intents, Message
from dotenv import load_dotenv

from nlu.chatbot import Chatbot

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")

intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)


chatbot = Chatbot(
    "output/savedmodels/order_entity_v4.h5",
    "output/savedmodels/customer_info_entity_v1.h5",
    "output/savedmodels/intents_v2.bin",
    "src/nlu/responses.json",
)


async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print("(Message was empty because intents were not enabled probably)")
        return

    if is_private := user_message[0] == "?":
        user_message = user_message[1:]

    try:
        response: str = chatbot.handle_message(user_message)
        (await message.author.send(response) if is_private else await message.channel.send(response))
    except Exception as e:
        print(e)


@client.event
async def on_ready() -> None:
    print(f"{client.user} is now running!")


@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    await send_message(message, user_message)


def main() -> None:
    client.run(token=TOKEN)


if __name__ == "__main__":
    main()

from nlu.pizzatalk_chatbot import PizzaTalkChatbot

chatbot = PizzaTalkChatbot(
    "output/savedmodels/order_entity_v2.h5",
    "output/savedmodels/intents_v2.bin",
    "src/nlu/responses.json",
)

print("model up")
while True:
    user_message = input()
    print(chatbot.handle_message(user_message))

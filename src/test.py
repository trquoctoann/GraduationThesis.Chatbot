from nlu.chatbot import Chatbot

chatbot = Chatbot(
    "output/savedmodels/order_entity_v4.h5",
    "output/savedmodels/customer_info_entity_v1.h5",
    "output/savedmodels/intents_v2.bin",
    "src/nlu/responses.json",
)

print("model up")
while True:
    user_message = input()
    response = chatbot.handle_message(user_message)
    print(response)

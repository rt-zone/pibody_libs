import urequests as requests

class Telegram:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        
    def send_message(self, message, topic_id=None):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }
        if topic_id is not None:
            payload["message_thread_id"] = topic_id
        response = requests.post(url, json=payload)
        print("Message sent:", response)
        # return response.json()

    def request_data(self):
        request = requests.get(f"{self.base_url}/getUpdates?offset={self.offset}").json()
        data = request['result']
        if not data:
            return False
        data = data[0]
        self.offset = data['update_id'] + 1
        text = data['message']['text']
        return text
        
    

    

# def request_data():
#     global OFFSET
    
#     request = requests.get(requestURL + "?offset=" + str(OFFSET)).json()
#     data = request['result']
#     if data == []:
#         return False
#     data=data[0]
#     OFFSET = data['update_id'] + 1
#     chat_id = data['message']['chat']['id']
#     text = data['message']['text']
#     return (chat_id, text)

# def send_message (chatId, message):
#     rp2.PIO(0).remove_program()
#     requests.post(sendURL + "?chat_id=" + str(chatId) + "&text=" + message)
#     print("Message sent")


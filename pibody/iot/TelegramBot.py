import urequests as requests

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    def send_message(self, message, chat_id, topic_id=None):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
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
        
    

    
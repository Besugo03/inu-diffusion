from hugchat_test import hugchat
from hugchat.login import Login
from dotenv import load_dotenv
import os

load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWD = os.getenv("PASSWD")

cookie_path_dir = "./cookies/" # NOTE: trailing slash (/) is required to avoid errors
sign = Login(EMAIL, PASSWD)
cookies = sign.login(cookie_dir_path=cookie_path_dir, save_cookies=True)

# Create your ChatBot
chatbot = hugchat.ChatBot(cookies=cookies.get_dict())  # or cookie_path="usercookies/<email>.json"

# Non stream response
query_result = chatbot.chat("who are you?")
print(query_result) # or query_result.text or query_result["text"]
chatbot.delete_conversation()
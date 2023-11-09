from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
import requests
import os
import time
import base64
from dotenv import load_dotenv
from Crypto.Hash import HMAC, SHA512
from inky.auto import auto
import sys
from PIL import Image, ImageFont, ImageDraw

load_dotenv()

# USERNAME = os.getenv("JUSTCAST_USERNAME")
# PASSWORD = os.getenv("JUSTCAST_PASSWORD")

# payload = {
#     "email": USERNAME,
#     "password": PASSWORD
# }

# # response = s.get(validate_url)
# # print(response.status_code)

# # response = s.get(metrics_url)
# # print(response.status_code)

# # soup = bs(response.content, "html.parser")
# # print(soup.prettify())
# # protected_content = soup.find(attrs={"id": "pageName"})
# # print(protected_content)

# # page = urlopen(test_url4)

# # html_bytes = page.read()
# # html = html_bytes.decode("utf-8")
# # print(html)

# import time,requests
# import hashlib,hmac,base64

# api_key = os.getenv("ICONOMI_API_KEY")
# api_secret = os.getenv("ICONOMI_SECRET_KEY")

# defaut_encoding = "utf8"

# uri = "https://api.iconomi.com"
# requestPath = "/v1/user/balance"
# api_url_target = iconomi_uri+request_path # https://api.iconomi.com/v1/user/balance
# method="GET"
# body=""
# icn_timestamp = int(1000.*time.time())

# message = (str(ICN_TIMESTAMP) + method.upper() + request_path + body).encode()
# signature_digest = HMAC.new(ICN_SECRET.encode(), ICN_SIGN, SHA512).digest() #here digest is byte
# b64_signature_digest= base64.b64encode(h.digest()).decode()

# headers_sign= {
#     "ICN-API-KEY":ICN_API_KEY,
#     "ICN-SIGN":encoded,
#     "ICN-TIMESTAMP":str(ICN_TIMESTAMP)
# }

# s=requests.session()
# res = s.get(iconomi_url,headers=headers,timeout=3, verify=True).content
# print (res)

# test_url = "https://dashboard.justcast.com/signin"
# test_url3 = "https://dashboard.justcast.com/dashboard"
# test_url4 = "http://testphp.vulnweb.com/userinfo.php"
# login_url = "https://justcastbe-migration.onrender.com/auth/sign_in"
# metrics_url = "https://dashboard.justcast.com/shows/40816/metrics"
# episode_url = "https://dashboard.justcast.com/shows/40816/metrics_episode_breakdown"
# validate_url = "https://justcastbe-migration.onrender.com/auth/validate_token"
# op3_url = "https://op3.dev/api/1/shows/" + os.getenv("PODCAST_GUID") + "?token=" + os.getenv("OP3_BEARER_TOKEN")
class InkyDisplay:
    if os.getenv("ENV") == 'prod':
        inky_display = auto(ask_user=True, verbose=True)
    else:
        print("No display found.")


class IconomiWallet:
    # Grab secret key from .env file
    ICN_SECRET = os.getenv("ICONOMI_SECRET_KEY")
    # Grab API key from .env file
    ICN_API_KEY = os.getenv("ICONOMI_API_KEY")
    # Store API URL
    iconomi_uri = 'https://api.iconomi.com'
    # HTTP Request Method
    method = 'GET'
    # HTTP Request Path
    request_path = '/v1/user/balance'
    # # Create Wallet object
    # wallet = {}
    # wallet.balance = 0

    def __init__(self):
        self.get_iconomi_balance()


    def create_signature(self):
        # Create timestamp for Iconomi API Request
        self.ICN_TIMESTAMP = int(1000.*time.time())
        # Create full URL for Iconomi HTTP API request
        self.iconomi_url = self.iconomi_uri + self.request_path
        # As request method is get, normally no request body is needed
        body = ''
        # Create signature using above data
        unencoded = (str(self.ICN_TIMESTAMP) + self.method + self.request_path + body).encode("utf-8")
        # Encode signature using secret key and SHA512
        h = HMAC.new(self.ICN_SECRET.encode(), unencoded, digestmod=SHA512)
        # Encode signature using base64
        self.ICN_SIGN = base64.b64encode(h.digest()).decode("utf-8")

    def create_headers(self):
        self.headers = {
            "ICN-API-KEY": self.ICN_API_KEY,
            "ICN-SIGN": self.ICN_SIGN,
            "ICN-TIMESTAMP": str(self.ICN_TIMESTAMP),
        }

    def create_session(self):
        self.s = requests.Session()

    def request_iconomi_balance(self):
        self.response = self.s.get(
            self.iconomi_url,
            headers=self.headers,
            timeout=3,
            verify=True
        )

    def get_iconomi_balance(self):
        self.create_signature()
        self.create_headers()
        
        self.create_session()

        self.request_iconomi_balance()

        if self.response.status_code == 200:
            self.wallet = self.response.json()
            self.wallet["balance"] = 0
            print(self.wallet)
            for index in self.wallet["daaList"]:
                self.wallet['balance'] += float(index["value"])

            for asset in self.wallet['assetList']:
                self.wallet['balance'] += float(asset["value"])

            self.wallet['balance'] = int(self.wallet['balance'])
        
        # return self.wallet.balance

def test():
    pass

def main():
    iconomi_wallet = IconomiWallet()
    if os.getenv("ENV") == 'dev':
        print(iconomi_wallet.wallet['balance'])
    elif os.getenv("ENV") == 'prod':
        print(iconomi_wallet.wallet['balance'])
    else:
        print('Environment not set.')
    



if __name__ == "__main__":
    main()
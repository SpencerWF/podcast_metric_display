from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
import requests
import os
import time
import base64
from dotenv import load_dotenv
from Crypto.Hash import HMAC, SHA512

load_dotenv()

# USERNAME = os.getenv("JUSTCAST_USERNAME")
# PASSWORD = os.getenv("JUSTCAST_PASSWORD")

# payload = {
#     "email": USERNAME,
#     "password": PASSWORD
# }

# Create timestamp for Iconomi API Request
ICN_TIMESTAMP = int(1000.*time.time())
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
# Create full URL for Iconomi HTTP API request
iconomi_url = iconomi_uri + request_path
# As request method is get, normally no request body is needed
body = ''
# Create signature using above data
ICN_SIGN = (str(ICN_TIMESTAMP) + method + request_path + body).encode("utf-8")
# print(ICN_SIGN)
# Encode signature using secret key and SHA512
h = HMAC.new(ICN_SECRET.encode(), ICN_SIGN, digestmod=SHA512)
# Encode signature using base64
encoded = base64.b64encode(h.digest()).decode("utf-8")
# print(encoded)

# Create headers for Iconomi HTTP API request
headers = {
    "ICN-API-KEY": ICN_API_KEY,
    "ICN-SIGN": encoded,
    "ICN-TIMESTAMP": str(ICN_TIMESTAMP),
}
# test_url = "https://dashboard.justcast.com/signin"
# test_url3 = "https://dashboard.justcast.com/dashboard"
# test_url4 = "http://testphp.vulnweb.com/userinfo.php"
# login_url = "https://justcastbe-migration.onrender.com/auth/sign_in"
# metrics_url = "https://dashboard.justcast.com/shows/40816/metrics"
# episode_url = "https://dashboard.justcast.com/shows/40816/metrics_episode_breakdown"
# validate_url = "https://justcastbe-migration.onrender.com/auth/validate_token"
# op3_url = "https://op3.dev/api/1/shows/" + os.getenv("PODCAST_GUID") + "?token=" + os.getenv("OP3_BEARER_TOKEN")

# Create session object
s = requests.Session()
# Send login request using headers created above
response = s.get(
    iconomi_url,
    headers=headers,
    timeout=3,
    verify=True
)

# Response status code and content
print(response.status_code)
print(response.content)

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
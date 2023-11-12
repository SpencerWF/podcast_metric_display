from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
import requests
import os
import time
import base64
from dotenv import load_dotenv
from Crypto.Hash import HMAC, SHA512
from inky.auto import auto
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw

load_dotenv()
PATH = os.path.dirname(__file__)

if(os.getenv("ENV") == 'dev'):
    from inky.mock import InkyMockPHAT as mock
    import schedule


# s=requests.session()
# res = s.get(iconomi_url,headers=headers,timeout=3, verify=True).content
# print (res)

# op3_url = "https://op3.dev/api/1/shows/" + os.getenv("PODCAST_GUID") + "?token=" + os.getenv("OP3_BEARER_TOKEN")

class InkyDisplay:

    def __init__(self):
        if os.getenv("ENV") == 'prod':
            self.inky_display = auto(ask_user=True, verbose=True)
        else:
            print("No display found")
            if(os.getenv("ENV") == 'dev'):
                print("Mocking display")
                self.inky_display = mock(colour="yellow")
                self.inky_display.resolution = (250, 122)
                self.inky_display.set_border(self.inky_display.WHITE)
                self.inky_display.show()

        self.img = Image.new("P", (self.inky_display.WIDTH, self.inky_display.HEIGHT))
        self.create_mask([0, 1, 2])

    def push_image(self):
        self.inky_display.set_image(self.img)
        self.inky_display.show()

    def create_mask(self, mask=[0, 1, 2]):
        """Create a transparency mask.

        Takes a paletized source image and converts it into a mask
        permitting all the colours supported by Inky pHAT (0, 1, 2)
        or an optional list of allowed colours.
        :param mask: Optional list of Inky pHAT colours to allow.
        """
        source = Image.open(os.path.join(PATH, "resources/calendar.png"))
        # source = Image.new("P", (self.inky_display.WIDTH, self.inky_display.HEIGHT))
        self.mask_image = Image.new("1", source.size)
        w, h = source.size
        for x in range(w):
            for y in range(h):
                p = source.getpixel((x, y))
                if p in mask:
                    self.mask_image.putpixel((x, y), 255)

    def print_digit(self, position, digit, colour):
        """Print a single digit using the sprite sheet.

        Each number is grabbed from the masked sprite sheet,
        and then used as a mask to paste the desired colour
        onto Inky pHATs image buffer.
        """
        o_x, o_y = position

        num_margin = 2
        num_width = 6
        num_height = 7

        s_y = 11
        s_x = num_margin + (digit * (num_width + num_margin))

        sprite = self.mask_image.crop((s_x, s_y, s_x + num_width, s_y + num_height))

        self.img.paste(colour, (o_x, o_y), sprite)


    def print_number(self, position, number, colour):
        """Print a number using the sprite sheet."""
        for digit in str(number):
            self.print_digit(position, int(digit), colour)
            position = (position[0] + 8, position[1])


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


iconomi_wallet = IconomiWallet()
display = InkyDisplay()
size = (250, 122)

def create_image():
    display.print_number((10, 10), iconomi_wallet.wallet['balance'], display.inky_display.YELLOW)

def update_display():
    iconomi_wallet.get_iconomi_balance()
    create_image()
    display.push_image()

def mock_loop():
    schedule.every(1).minutes.do(update_display)

    while True:
        schedule.run_pending()
        time.sleep(1)


def test():
    pass

def main():
    if os.getenv("ENV") == 'dev':
        mock_loop()
    elif os.getenv("ENV") == 'prod':
        update_display()
        print(iconomi_wallet.wallet['balance'])
    else:
        print('Environment not set.')
    



if __name__ == "__main__":
    main()
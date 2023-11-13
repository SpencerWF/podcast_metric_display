from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
import requests
import os
import time
import base64
from dotenv import load_dotenv
from Crypto.Hash import HMAC, SHA512
from inky.auto import auto
from inky import InkyPHAT_SSD1608
from PIL import Image, ImageFont, ImageDraw

load_dotenv()
PATH = os.path.dirname(__file__)

if(os.getenv("ENV") == 'dev'):
    from inky.mock import InkyMockPHATSSD1608 as mock
    import schedule


# s=requests.session()
# res = s.get(iconomi_url,headers=headers,timeout=3, verify=True).content
# print (res)

# op3_url = "https://op3.dev/api/1/shows/" + os.getenv("PODCAST_GUID") + "?token=" + os.getenv("OP3_BEARER_TOKEN")

class InkyDisplay:

    def __init__(self):
        if os.getenv("ENV") == 'prod':
            self.inky_display = auto(ask_user=True, verbose=True)
            print("Found display: {}".format(self.inky_display.resolution))
        else:
            print("No display found")
            if(os.getenv("ENV") == 'dev'):
                print("Mocking display")
                self.inky_display = mock(colour="yellow")
                self.inky_display.set_border(self.inky_display.WHITE)
                self.inky_display.show()

        self.img = Image.open(os.path.join(PATH, "resources/background.png"))
        self.create_mask([0])

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

        source = Image.open(os.path.join(PATH, "resources/numbers.png"))
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
        num_width = 14
        num_height = 16

        s_y = 2
        s_x = num_margin + (digit * (num_width + num_margin))

        sprite = self.mask_image.crop((s_x, s_y, s_x + num_width, s_y + num_height))

        self.img.paste(colour, (o_x, o_y), sprite)


    def print_number(self, position, number, colour):
        """Print a number using the sprite sheet."""
        print(f'Printing {number} to screen')
        for digit in str(number):
            self.print_digit(position, int(digit), colour)
            position = (position[0] + 16, position[1])


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

    split = [
        {
            "id": "",
            "value": 0,
        },
        {
            "id": "",
            "value": 0,
        }
    ]
    # # Create Wallet object
    # wallet = {}
    # wallet.balance = 0

    def __init__(self):
        self.get_iconomi_balance()
        self.get_iconomi_split()


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

    def get_iconomi_split(self):
        self.split = [
            {
                "id": "",
                "value": 0,
            },
            {
                "id": "",
                "value": 0,
            }
        ]

        for index in self.wallet["daaList"]:
            if self.split[0]["value"] < float(index["value"]):
                self.split[1]["value"] = self.split[0]["value"]
                self.split[1]["id"] = self.split[0]["id"]
                self.split[0]["value"] = float(index["value"])
                self.split[0]["id"] = index["ticker"]
            elif self.split[1]["value"] < float(index["value"]):
                self.split[1]["value"] = float(index["value"])
                self.split[1]["id"] = index["ticker"]

        for index in self.wallet["assetList"]:
            if float(self.split[0]["value"]) < float(index["value"]):
                self.split[1]["value"] = self.split[0]["value"]
                self.split[1]["id"] = self.split[0]["id"]
                self.split[0]["value"] = float(index["value"])
                self.split[0]["id"] = index["ticker"]
            elif self.split[1]["value"] < float(index["value"]):
                self.split[1]["value"] = float(index["value"])
                self.split[1]["id"] = index["ticker"]

        self.split_total = self.split[0]["value"] + self.split[1]["value"]

class PodcastStats:
    name = "Founder's Voyage"
    op3_url = "https://op3.dev/api/1/shows/" + os.getenv("PODCAST_GUID") + "?token=" + os.getenv("OP3_BEARER_TOKEN") + "&episodes=include"
    op3_downloads = "https://op3.dev/api/1/downloads/show/" 

    def __init__(self):
        self.get_op3_stats()
        self.get_download_split()

    def get_op3_stats(self):
        self.response = requests.get(self.op3_url, timeout=3, verify=True).json()
        print(f'Looking up stats for {self.response["title"]}')
        continuationToken = 0
        continuationFlag = True
        self.total_downloads = 0
        while continuationFlag:
            extra = ''
            if continuationToken > 0:
                extra = '&continuationToken=' + str(continuationToken) + "&format=json"
            else:
                extra = "&format=json"
        
            self.op3_downloads += self.response["showUuid"] + "?token=" + os.getenv("OP3_BEARER_TOKEN") + extra
            self.stats = requests.get(self.op3_downloads , timeout=10, verify=True).json()
            if 'count' in self.stats.keys():
                self.total_downloads += self.stats['count']
                if 'continuationToken' in self.stats.keys():
                    continuationToken = self.stats['continuationToken']
                else:
                    continuationFlag = False
            else:
                continuationFlag = False
                print('No stats found')
                print(self.stats.keys())
                print(self.stats['error'])

    def get_download_split(self):
        self.latest_episode = self.response['episodes'][0]
        self.latest_downloads = 0
        print(self.latest_episode)
        for download in self.stats['rows']:
            print(f'Download time: {download["time"]} - Episode time: {self.latest_episode["pubdate"]}')
            if download['time'] > self.latest_episode['pubdate']:
                if download['episodeId'] == self.latest_episode['id']:
                    self.latest_downloads += 1
            else:
                break

        print(f'Latest episode has {self.latest_downloads} downloads of {self.total_downloads} total downloads')

    def get_total_downloads(self):
        return self.total_downloads

iconomi_wallet = IconomiWallet()
podcast_stats = PodcastStats()
display = InkyDisplay()
size = (250, 122)

def create_image():
    display.img = Image.open(os.path.join(PATH, "resources/background.png"))
    display.create_mask([0])

    draw = ImageDraw.Draw(display.img)
    display.print_number((26, 24), iconomi_wallet.wallet['balance'], display.inky_display.YELLOW)

    # Draw pie chart of the two largest Iconomi holdings to see the split
    draw.pieslice((100,25, 125, 50), 0, 360, fill=display.inky_display.BLACK, outline=display.inky_display.BLACK)
    first_split = round(int(iconomi_wallet.split[0]["value"] / int(iconomi_wallet.split_total) * 360))
    draw.pieslice((101, 26, 124, 49), 0, first_split, fill=display.inky_display.YELLOW)
    draw.pieslice((101, 26, 124, 49), first_split, 360, fill=display.inky_display.WHITE)

    display.print_number((26, 80), podcast_stats.total_downloads, display.inky_display.YELLOW)

    # Draw rectangle showing split between latest episodes and total downloads
    draw.rectangle((100, 82, 130, 97), fill=display.inky_display.BLACK, outline=display.inky_display.BLACK)
    draw.rectangle((101, 83, 101+30*podcast_stats.latest_downloads/podcast_stats.total_downloads, 96), fill=display.inky_display.YELLOW, outline=display.inky_display.YELLOW)
    draw.rectangle((101+30*podcast_stats.latest_downloads/podcast_stats.total_downloads, 83, 129, 96), fill=display.inky_display.WHITE, outline=display.inky_display.WHITE)

def update_instances():
    iconomi_wallet.get_iconomi_balance()
    iconomi_wallet.get_iconomi_split()
    podcast_stats.get_op3_stats()
    podcast_stats.get_download_split()

def update_display():
    create_image()
    display.inky_display.set_border(display.inky_display.BLACK)
    display.push_image()

def mock_loop():
    schedule.every(1).minutes.do(update_instances)
    schedule.every(1).minutes.do(update_display)

    while True:
        schedule.run_pending()
        time.sleep(1)


def test():
    pass

def main():
    if os.getenv("ENV") == 'dev':
        update_display()
        mock_loop()
    elif os.getenv("ENV") == 'prod':
        update_display()
        print(iconomi_wallet.wallet['balance'])
    else:
        print('Environment not set.')

if __name__ == "__main__":
    main()
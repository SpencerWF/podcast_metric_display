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
import math
from discord_webhook import DiscordWebhook, DiscordEmbed
import json

load_dotenv()
PATH = os.path.dirname(__file__)

if(os.getenv("ENV") == 'dev'):
    from inky.mock import InkyMockPHATSSD1608 as mock
    import schedule

MID_TRIANGLE_SIZE = 20
HTTP_OK = 200
ICONOMI_NUMBERS_POSITION = (65, 12)
SHARKNINJA_NUMBERS_POSITION = (65, 56)
PODCAST_NUMBERS_POSITION = (35, 100)
OUTLINE_PIESLICE = (100,25, 125, 50)
FIRST_PIECE_PIESLICE = (101, 26, 124, 49)
SECOND_PIECE_PIESLICE = (101, 26, 124, 49)
FULL_CIRCLE = 360
FIRST_TRIANGLE_START = 100
SECOND_TRIANGLE_START = 101
THIRD_TRIANGLE_START_WIDTH = 102
TRIANGLE_START_HEIGHT = 112

USD_to_GBP = 0.72

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

# class CurrencyConvertion:


#     def __init__(self):
#         date = time.strftime("%Y-%m-%d", time.localtime(time.time() - 18000))
#         file_name = f'{date}.json'
#         if os.path.isfile(f'./resources/{file_name}'):
#             with open(os.path.join(PATH, f'resources/{file_name}'), "wr") as f:
#                 self.stock_currency = json.load(f)
#                 USD_to_GBP = self.stock_currency['currency']['USD']
#         else:
#             json_file = json.dumps(self.stock_currency)
#             with open(os.path.join(PATH, f'resources/{file_name}'), "w") as f:
#                 f.write(json_file)

class StocksWallet:
    # Grab Alpha Vantage API key from .env file
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    # Store API URL
    ALPHA_VANTAGE_URL = os.getenv("ALPHA_VANTAGE_URL")

    # Grab API key from .env file
    CURRENCY_API_KEY = os.getenv("FIXER_API_KEY")
    # Store API URL
    CURRENCY_URL = os.getenv("FIXER_URL")
    # Store currency symbols
    CURRENCY_SYMBOLS = os.getenv("FIXER_SYMBOLS")

    def __init__(self):
        self.get_stock_list()

    def __str__(self) -> str:
        return f"Stocks: {self.stock_list}"

    def get_stock_list(self):
        date = time.strftime("%Y-%m-%d", time.localtime(time.time() - 18000))
        file_name = f'{date}.json'
        if os.path.isfile(f'./resources/{file_name}'):
            with open(os.path.join(PATH, f'resources/{file_name}'), "r") as f:
                self.stock_list = json.load(f)
        
        else:
            self.stock_list = {
                "stocks": {
                    "SN": {
                        "symbol": "SN",
                        "stock_count": 116,
                        "currency": "USD",
                        "price": 0,
                        "value": 0
                    },
                    'value': 0
                },
                "currency": {
                    "USD": 0,
                    "AUD": 0,
                    "GBP": 1
                },
                "error": 0
            }

            self.get_currency_conversion()
            print(f"Stock list: {self.stock_list}")
            for stock in self.stock_list['stocks']:
                if stock != 'value':
                    print(f"Getting stock price for {stock}")
                    try:
                        self.get_stock_price(stock)
                        self.stock_list['stocks']['value'] += self.stock_list['stocks'][stock]['value']
                    except Exception as e:
                        print(f"Error: {e}")

            json_file = json.dumps(self.stock_list)
        
            with open(os.path.join(PATH, f'resources/{file_name}'), "w") as f:
                f.write(json_file)

    def get_currency_conversion(self):
        global USD_to_GBP
        self.currency_url = f"{self.CURRENCY_URL}{self.CURRENCY_API_KEY}"
        print(f"Currency conversion URL: {self.currency_url}")
        self.response = requests.get(self.currency_url, timeout=3, verify=True).json()
        print(f"Currency conversion: {self.response}")
        if 'error' in self.response.keys():
            print(f"Error self.response['error']['code']: {self.response['error']['info']}")
            self.stock_list['error'] = self.response['error']['code']
        else:
            self.stock_list['error'] = 0;
            self.stock_list['currency']['USD'] = self.response['rates']['GBP']/self.response['rates']['USD']
            USD_to_GBP = self.stock_list['currency']['USD']
            self.stock_list['currency']['AUD'] = self.response['rates']['AUD']/self.response['rates']['GBP']
            self.stock_list['currency']['GBP'] = self.response['rates']['GBP']/self.response['rates']['GBP']
            print(f"Currency conversion: {self.stock_list['currency']}")

    def get_stock_price(self, stock):
        if self.response['error']['code'] == 0:
            self.stock_url = f"{self.ALPHA_VANTAGE_URL}{self.stock_list['stocks'][stock]['symbol']}&apikey={self.ALPHA_VANTAGE_API_KEY}"
            self.response = requests.get(self.stock_url, timeout=3, verify=True).json()
            print(self.response)
            last_refreshed = self.response['Meta Data']['3. Last Refreshed']
            self.stock_list['stocks'][stock]['price'] = float(self.response['Time Series (Daily)'][last_refreshed]['4. close'])
            self.stock_list['stocks'][stock]['value'] = float(self.stock_list['stocks'][stock]['price']) * float(self.stock_list['stocks'][stock]['stock_count']) * float(self.stock_list['currency'][self.stock_list['stocks'][stock]['currency']])
            self.stock_list['stocks'][stock]['value'] = int(self.stock_list['stocks'][stock]['value'])
            print(f"Stock {self.stock_list['stocks'][stock]['symbol']} has a price of {self.stock_list['stocks'][stock]['price']} and a value of {self.stock_list['stocks'][stock]['value']} USD")
        elif self.response['error']['code'] == 104:
            print("API limit reached")
        else:
            print("Unknown Error")

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
        print(f"Requesting Iconomi balance from {self.iconomi_url}")
        print(f'Headers {self.headers}')
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
        print(
            f"Requesting Iconomi balance with status code: {self.response.status_code}"
        )

        if self.response.status_code == HTTP_OK:
            self.wallet = self.response.json()
            self.wallet["balance"] = 0
            print(self.wallet)
            for index in self.wallet["daaList"]:
                self.wallet['balance'] += float(index["value"])

            for asset in self.wallet['assetList']:
                self.wallet['balance'] += float(asset["value"])

            self.wallet['balance'] = int(float(self.wallet['balance']) * USD_to_GBP)
        else:
            print(f"Error: {self.response.status_code}")
            self.wallet = {
                "balance": 1,
                "daaList": [],
                "assetList": []
            }

        
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
    font = ImageFont.truetype(os.path.join(PATH, "resources/bnfont.ttf"), 24)

    def __init__(self):
        self.get_op3_stats()
        if self.response != 1:
            self.get_download_split()

    def get_op3_stats(self):
        self.total_downloads = 0
        if os.getenv('PODCAST_REQUEST') == 'true':
            self.response = requests.get(self.op3_url, timeout=3, verify=True).json()
            print(f'Looking up stats for {self.response["title"]}')
            continuationToken = 0
            continuationFlag = True
            self.total_downloads = 0
            self.op3_downloads = "https://op3.dev/api/1/downloads/show/"
            while continuationFlag:
                extra = ''
                if continuationToken != 0:
                    extra = '&continuationToken=' + str(continuationToken) + "&format=json"
                else:
                    extra = "&format=json"
            
                self.op3_downloads += self.response["showUuid"] + "?token=" + os.getenv("OP3_BEARER_TOKEN") + extra
                self.stats = requests.get(self.op3_downloads , timeout=20, verify=True).json()
                if 'count' in self.stats.keys():
                    self.total_downloads += self.stats['count']
                    if 'continuationToken' in self.stats.keys():
                        print(f'Continuation token: {self.stats["continuationToken"]} with {self.stats["count"]} downloads')
                        continuationToken = self.stats['continuationToken']
                    else:
                        print('No continuation token with ' + str(self.stats['count']) + ' downloads')
                        continuationFlag = False
                else:
                    continuationFlag = False
                    print('No stats found')
                    print(self.stats.keys())
                    print(self.stats['error'])
        else:
            self.response = 1
            print('Not requesting podcast stats')

        # print(f'Rows: {len(self.stats["rows"])}')

    def get_download_split(self):
        self.latest_episode = self.response['episodes'][0]
        self.latest_episode_time = time.mktime(time.strptime(self.latest_episode['pubdate'], "%Y-%m-%dT%H:%M:%S.%fZ"))
        self.week1_downloads = 0
        self.week2_downloads = 0
        self.week3_downloads = 0
        self.week1_latest_downloads = 0
        self.week2_latest_downloads = 0
        self.week3_latest_downloads = 0
        
        print(self.latest_episode)

        # Get current time in epoch seconds
        current_date = time.time()
        print(current_date)
        
        for download in reversed(self.stats['rows']):
            download_time = time.mktime(time.strptime(download['time'], "%Y-%m-%dT%H:%M:%S.%fZ"))
            
            # If download is within the last week
            if download_time > current_date - 604800:
                self.week1_downloads += 1
                if download['episodeId'] == self.latest_episode['id']:
                    self.week1_latest_downloads += 1

            # If download is within the last two weeks
            elif download_time > current_date-2 * 604800:
                self.week2_downloads += 1
                if download['episodeId'] == self.latest_episode['id']:
                    self.week2_latest_downloads += 1

            # If download is within the last three weeks
            elif download_time > current_date-3 * 604800:
                self.week3_downloads += 1
                if download['episodeId'] == self.latest_episode['id']:
                    self.week3_latest_downloads += 1
            else:
                break

        print(f'Week 1: {self.week1_downloads} downloads Latest: {self.week1_latest_downloads}')
        print(f'Week 2: {self.week2_downloads} downloads Latest: {self.week2_latest_downloads}')
        print(f'Week 3: {self.week3_downloads} downloads Latest: {self.week3_latest_downloads}')
        # print(f'Latest episode has {self.latest_downloads} downloads of {self.total_downloads} total downloads')

    def get_total_downloads(self):
        return self.total_downloads
    
    def craft_discord_update(self):
        self.webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK"))
        embed = DiscordEmbed(title=f'{self.name} Stats', description=f'Total Downloads: {self.total_downloads}', color=242424)
        embed.set_author(name='Founder\'s Voyage', url='https://foundersvoyage.com', icon_url='https://custom-images.strikinglycdn.com/res/hrscywv4p/image/upload/c_limit,fl_lossy,h_300,w_300,f_auto,q_auto/4011783/807815_706925.png')
        # embed.set_image(url='resources/discord_message.png')
        embed.set_timestamp()
        with open(os.path.join(PATH, "resources/discord_message.png"), "rb") as f:
            embed.set_image(url="attachment://discord_message.png")
            self.webhook.add_file(file=f.read(), filename='discord_message.png')
        self.webhook.add_embed(embed)

        self.message = {
            "content": f'Founder\'s Voyage Total Downloads: {str(self.total_downloads)} \n',
            "username": "Founder's Voyage",
        }

stocks_wallet = StocksWallet()
iconomi_wallet = IconomiWallet()
podcast_stats = PodcastStats()
#FIXME: Move below to daily section to avoid API limit
display = InkyDisplay()
# discord_display = InkyDisplay()
size = (250, 122)

def create_image():
    display.img = Image.open(os.path.join(PATH, "resources/background.png"))
    display.create_mask([0])

    draw = ImageDraw.Draw(display.img)
    display.print_number(ICONOMI_NUMBERS_POSITION, iconomi_wallet.wallet['balance'], display.inky_display.YELLOW)

    display.print_number(SHARKNINJA_NUMBERS_POSITION, stocks_wallet.stock_list['stocks']['value'], display.inky_display.YELLOW)

    display.print_number(PODCAST_NUMBERS_POSITION, podcast_stats.total_downloads, display.inky_display.YELLOW)

    # Draw triangles to show the split of downloads for the last 3 weeks
    if hasattr(podcast_stats, 'week2_downloads') == False or podcast_stats.week2_downloads == 0:
        podcast_stats.week2_downloads = 1

    week1_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week1_downloads/podcast_stats.week2_downloads))
    week1_latest_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week1_latest_downloads/podcast_stats.week2_downloads))
    week2_latest_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week2_latest_downloads/podcast_stats.week2_downloads))
    week3_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week3_downloads/podcast_stats.week2_downloads))
    week3_latest_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week3_latest_downloads/podcast_stats.week2_downloads))

    draw.polygon([(THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE, TRIANGLE_START_HEIGHT), (THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE + week1_size, TRIANGLE_START_HEIGHT), (THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE + week1_size, TRIANGLE_START_HEIGHT - week1_size)], fill=display.inky_display.YELLOW, outline=display.inky_display.YELLOW)
    draw.polygon([(THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE + week1_size - week1_latest_size, TRIANGLE_START_HEIGHT), (THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE + week1_size, TRIANGLE_START_HEIGHT), (THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE+ week1_size, TRIANGLE_START_HEIGHT - week1_latest_size)], fill=display.inky_display.WHITE, outline=display.inky_display.WHITE)

    draw.polygon([(SECOND_TRIANGLE_START + week3_size, TRIANGLE_START_HEIGHT), (SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE, TRIANGLE_START_HEIGHT), (SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE, TRIANGLE_START_HEIGHT - MID_TRIANGLE_SIZE)], fill=display.inky_display.YELLOW, outline=display.inky_display.YELLOW)
    draw.polygon([(SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE - week2_latest_size, TRIANGLE_START_HEIGHT), (SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE, TRIANGLE_START_HEIGHT), (SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE, TRIANGLE_START_HEIGHT - week2_latest_size)], fill=display.inky_display.WHITE, outline=display.inky_display.WHITE)

    draw.polygon([(FIRST_TRIANGLE_START, TRIANGLE_START_HEIGHT), (FIRST_TRIANGLE_START + week3_size, TRIANGLE_START_HEIGHT), (FIRST_TRIANGLE_START + week3_size, TRIANGLE_START_HEIGHT - week3_size)], fill=display.inky_display.YELLOW, outline=display.inky_display.YELLOW)
    draw.polygon([(FIRST_TRIANGLE_START + week3_size - week3_latest_size, TRIANGLE_START_HEIGHT), (FIRST_TRIANGLE_START + week3_size, TRIANGLE_START_HEIGHT), (FIRST_TRIANGLE_START + week3_size, TRIANGLE_START_HEIGHT - week3_latest_size)], fill=display.inky_display.WHITE, outline=display.inky_display.WHITE)
    # draw.rectangle((100, 82, 130, 97), fill=display.inky_display.BLACK, outline=display.inky_display.BLACK)
    # draw.rectangle((101, 83, 101+30*podcast_stats.latest_downloads/podcast_stats.total_downloads, 96), fill=display.inky_display.YELLOW, outline=display.inky_display.YELLOW)
    # draw.rectangle((101+30*podcast_stats.latest_downloads/podcast_stats.total_downloads, 83, 129, 96), fill=display.inky_display.WHITE, outline=display.inky_display.WHITE)
    # display.inky_display.

def create_discord_image():
    discord_img = Image.open(os.path.join(PATH, "resources/discord_background.png"))
    # display.create_mask([0])

    draw = ImageDraw.Draw(discord_img)
    # font = ImageFont

    # display.print_number((20, 32), podcast_stats.total_downloads, display.inky_display.YELLOW)
    draw.text((20, 40), str(podcast_stats.total_downloads), font=podcast_stats.font, fill=display.inky_display.YELLOW)
    
    # Draw triangles to show the split of downloads for the last 3 weeks
    if podcast_stats.week2_downloads == 0:
        podcast_stats.week2_downloads = 1
    
    week1_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week1_downloads/podcast_stats.week2_downloads))
    week3_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week3_downloads/podcast_stats.week2_downloads))
    week1_latest_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week1_latest_downloads/podcast_stats.week2_downloads))
    week2_latest_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week2_latest_downloads/podcast_stats.week2_downloads))
    week3_latest_size = MID_TRIANGLE_SIZE*(math.sqrt(podcast_stats.week3_latest_downloads/podcast_stats.week2_downloads))

    draw.polygon([(THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE, 70), (THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE + week1_size, 70), (THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE + week1_size, 70 - week1_size)], fill=display.inky_display.YELLOW, outline=display.inky_display.YELLOW)
    draw.polygon([(THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE + week1_size - week1_latest_size, 70), (THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE + week1_size, 70), (THIRD_TRIANGLE_START_WIDTH + week3_size + MID_TRIANGLE_SIZE + week1_size, 70 - week1_latest_size)], fill=display.inky_display.WHITE, outline=display.inky_display.WHITE)

    draw.polygon([(SECOND_TRIANGLE_START + week3_size, 70), (SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE, 70), (SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE, 70 - MID_TRIANGLE_SIZE)], fill=display.inky_display.YELLOW, outline=display.inky_display.YELLOW)
    draw.polygon([(SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE - week2_latest_size, 70), (SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE, 70), (SECOND_TRIANGLE_START + week3_size + MID_TRIANGLE_SIZE, 70 - week2_latest_size)], fill=display.inky_display.WHITE, outline=display.inky_display.WHITE)

    draw.polygon([(FIRST_TRIANGLE_START, 70), (FIRST_TRIANGLE_START + week3_size, 70), (FIRST_TRIANGLE_START + week3_size, 70 - week3_size)], fill=display.inky_display.YELLOW, outline=display.inky_display.YELLOW)
    draw.polygon([(FIRST_TRIANGLE_START + week3_size - week3_latest_size, 70), (FIRST_TRIANGLE_START + week3_size, 70), (FIRST_TRIANGLE_START + week3_size, 70 - week3_latest_size)], fill=display.inky_display.WHITE, outline=display.inky_display.WHITE)

    discord_img.save(os.path.join(PATH, "resources/discord_message.png"))
    # draw.rectangle((100, 82, 130, 97), fill=display.inky_display.BLACK, outline=display.inky_display.BLACK)
    # draw.rectangle((101, 83, 101+30*podcast_stats.latest_downloads/podcast_stats.total_downloads, 96), fill=display.inky_display.YELLOW, outline=display.inky_display.YELLOW)
    # draw.rectangle((101+30*podcast_stats.latest_downloads/podcast_stats.total_downloads, 83, 129, 96), fill=display.inky_display.WHITE, outline=display.inky_display.WHITE)


def update_instances():
    iconomi_wallet.get_iconomi_balance()
    if iconomi_wallet.response.status_code == HTTP_OK:
        iconomi_wallet.get_iconomi_split()
    podcast_stats.get_op3_stats()
    if podcast_stats.response != 1:
        podcast_stats.get_download_split()

def update_display():
    create_image()
    # display.inky_display.set_border(display.inky_display.BLACK)
    display.push_image()

def discord_update():
    create_discord_image()
    podcast_stats.craft_discord_update()
    response = podcast_stats.webhook.execute()
    print(response)
    # requests.post(os.getenv("DISCORD_WEBHOOK"), json=podcast_stats.message)

def mock_loop():
    schedule.every(1).minutes.do(update_instances)
    schedule.every(1).minutes.do(update_display)
    schedule.every(1).minutes.do(discord_update)
    # schedule.every(1).day.at("05:00").do(discord_update)
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
        date = time.strftime("%Y-%m-%d", time.localtime(time.time() - 18000))
        file_name = f'{date}.log'
        if os.getenv("DISCORD_WEBHOOK") and not os.path.isfile(f'./resources/{file_name}'):
            print("Sending discord update")
            discord_update()
            # Get yesterday's date
            yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
            # Delete yesterday's log file
            os.path.isfile(f'./resources/{yesterday}') and os.remove(f'./resources/{yesterday}')
            # Create log file for today
            # open(file_name, 'w+').close()

        print(iconomi_wallet.wallet['balance'])
    else:
        print('Environment not set.')

if __name__ == "__main__":
    main()

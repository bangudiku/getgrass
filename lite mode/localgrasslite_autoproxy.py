import asyncio
import random
import ssl
import json
import time
import uuid
import base64
import aiohttp
from datetime import datetime
from colorama import init, Fore, Style
from websockets_proxy import Proxy, proxy_connect

init(autoreset=True)

BANNER = """
_________ ____________________                            
__  ____/______  /__  ____/____________ _______________
_  / __ _  _ \\  __/  / __ __  ___/  __ `/_  ___/_  ___/
/ /_/ / /  __/ /_ / /_/ / _  /   / /_/ /_(__  )_(__  ) 
\\____/  \\___/\\__/ \\____/  /_/    \\__,_/ /____/ /____/  
"""

EDGE_USERAGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.57",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.52",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.46",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.128",
]

HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created", 
    202: "Accepted",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden", 
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}

def colorful_log(proxy, device_id, message_type, message_content, is_sent=False, mode=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = Fore.GREEN if is_sent else Fore.BLUE
    action_color = Fore.YELLOW
    mode_color = Fore.LIGHTYELLOW_EX
    log_message = (
        f"{Fore.WHITE}[{timestamp}] "
        f"{Fore.MAGENTA}[Proxy: {proxy}] "
        f"{Fore.CYAN}[Device ID: {device_id}] "
        f"{action_color}[{message_type}] "
        f"{color}{message_content} "
        f"{mode_color}[{mode}]"
    )
    print(log_message)

async def fetch_proxies():
    url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            proxies = await response.text()
            return proxies.splitlines()

async def connect_to_wss(socks5_proxy, user_id, mode):
    device_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, socks5_proxy))
    random_user_agent = random.choice(EDGE_USERAGENTS)
    
    colorful_log(
        proxy=socks5_proxy,
        device_id=device_id,
        message_type="INITIALIZATION",
        message_content=f"User Agent: {random_user_agent}",
        mode=mode
    )

    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        uri_list = [
            "wss://proxy2.wynd.network:4444/",
            "wss://proxy2.wynd.network:4650/",
        ]
        uri = random.choice(uri_list)
        server_hostname = "proxy.wynd.network"
        proxy = Proxy.from_url(socks5_proxy)
        
        async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname) as websocket:
            async def send_ping():
                while True:
                    ping_message = json.dumps(
                        {"id": str(uuid.uuid4()), "action": "PING", "timestamp": int(time.time())}
                    )
                    await websocket.send(ping_message)
                    colorful_log(
                        proxy=socks5_proxy,
                        device_id=device_id,
                        message_type="SENDING PING",
                        message_content="Ping sent",
                        is_sent=True,
                        mode=mode
                    )
                    await asyncio.sleep(5)
            
            asyncio.create_task(send_ping())
            
            while True:
                response = await websocket.recv()
                message = json.loads(response)
                
                if message.get("action") == "PONG":
                    colorful_log(
                        proxy=socks5_proxy,
                        device_id=device_id,
                        message_type="PING SUCCESS",
                        message_content="Pong received",
                        mode=mode
                    )
                else:
                    colorful_log(
                        proxy=socks5_proxy,
                        device_id=device_id,
                        message_type="RECEIVED",
                        message_content=json.dumps(message),
                        mode=mode
                    )
    except Exception as e:
        colorful_log(
            proxy=socks5_proxy,
            device_id=device_id,
            message_type="ERROR",
            message_content=str(e),
            mode=mode
        )
        await asyncio.sleep(5)

async def main():
    print(f"{Fore.CYAN}{BANNER}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}IM-Hanzou | GetGrass Crooter V2{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}Select Mode:{Style.RESET_ALL}")
    print("1. Extension Mode")
    print("2. Desktop Mode")
    
    while True:
        mode_choice = input("Enter your choice (1/2): ").strip()
        if mode_choice in ['1', '2']:
            break
        print(f"{Fore.RED}Invalid choice. Please enter 1 or 2.{Style.RESET_ALL}")
    
    mode = "extension" if mode_choice == "1" else "desktop"
    print(f"{Fore.GREEN}Selected mode: {mode}{Style.RESET_ALL}")
    
    _user_id = input("Enter user ID: ").strip()
    proxies = await fetch_proxies()
    
    print(f"{Fore.YELLOW}Total Proxies: {len(proxies)}{Style.RESET_ALL}")
    tasks = [asyncio.ensure_future(connect_to_wss(proxy, _user_id, mode)) for proxy in proxies]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

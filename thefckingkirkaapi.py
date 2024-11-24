import aiohttp
import asyncio
import websockets
import json
import sys
import math
class KirkaAPI:
    def __init__(self, url=None):
        self.websocket = None
        self.url = url if url is not None else "kirka.io"

    # WebSocket affiliated Stuff

    async def connect_websocket(self, token=None):
        while True:
            try:
                if token:
                    self.websocket = await websockets.connect(f"wss://chat.{self.url}/", extra_headers={"Authorization": f"Bearer {token}"})
                else:
                    self.websocket = await websockets.connect(f"wss://chat.{self.url}/")

                print("WebSocket connection established.")
                await self.on_ready()
                
                async for message in self.websocket:
                    try: # prevent shitty code from crashing everything
                        message = json.loads(message)
                        if hasattr(self, 'on_message'):
                            await self.on_message(message)
                        if hasattr(self, 'trade_message'):
                            if message.get("type") == 13 and message.get("user") is None:
                                await self.trade_message(message)
                        if hasattr(self, 'trade_send'):
                            if message.get("type") == 13 and message.get("user") is None and "is offering their" in message.get("message", ""):
                                await self.trade_send(message)
                        if hasattr(self, 'trade_accepted'):
                            if message.get("type") == 13 and message.get("user") is None and "** accepted **" in message.get("message", "") and "**'s offer" in message.get("message", ""):
                                await self.trade_accepted(message)
                        if hasattr(self, 'trade_cancel'):
                            if message.get("type") == 13 and message.get("user") is None and "cancelled their trade" in message.get("message", ""):
                                await self.trade_cancel(message)
                    except KeyboardInterrupt:
                        if hasattr(self, "on_close"):self.on_close()
                        break

                    except Exception as e:
                        print(f"Error: {e}\nIgnoring...\n", file=sys.stderr)
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed. Attempting to reconnect...")
                await asyncio.sleep(5)  # Wait for 5 seconds before attempting to reconnect
            except Exception as e:
                print(f"Error: {e}\nAttempting to reconnect...\n", file=sys.stderr)
                await asyncio.sleep(5)  # Wait for 5 seconds before attempting to reconnect
    async def disconnect_websocket(self):
        if self.websocket and self.websocket.open:
            await self.websocket.close()
            print("WebSocket connection closed.")
    async def on_ready(self):
        pass

    async def send_global_chat(self, message):
        if not token:
            return "Not posting due to missing token!"
        if self.websocket and self.websocket.open:
            await self.websocket.send(message)
            return "POSTED MESSAGE"
        else:
            return "WebSocket is not open or not connected."
    def set_on_ready_handler(self,handler):
        self.on_ready = handler

    def set_trade_message_handler(self, handler):
        self.trade_message = handler
    def set_on_normal_message_handler(self,handler):
        self.on_normal_message = handler
    def set_on_trade_accepted(self, handler):
        self.trade_accepted = handler

    def set_on_trade_send(self, handler):
        self.trade_send = handler

    def set_on_trade_cancel(self, handler):
        self.trade_cancel = handler

    def set_on_close_handler(self, handler):
        self.on_close = handler

    def set_on_message_handler(self, handler):
        self.on_message = handler

    async def close_websocket(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    # User

    async def get_stats(self, short_id):
        try:
            short_id = short_id.upper().replace('#', '')
            async with aiohttp.ClientSession() as session:
                async with session.post(f"https://api.{self.url}/api/user/getProfile",
                                        headers={
                                            "accept": "application/json, text/plain, */*",
                                            "content-type": "application/json;charset=UTF-8",
                                        },
                                        json={"id": short_id, "isShortId": True}) as response:
                    return await response.json()
        except Exception as e:
            return str(e)

    async def get_stats_long_id(self, long_id):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"https://api.{self.url}/api/user/getProfile",
                                        headers={
                                            "accept": "application/json, text/plain, */*",
                                            "content-type": "application/json;charset=UTF-8",
                                        },
                                        json={"id": long_id}) as response:
                    return await response.json()
        except Exception as e:
            return str(e)

    async def get_my_profile(self, token):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.{self.url}/api/user",
                                       headers={
                                           "accept": "application/json, text/plain, */*",
                                           "authorization": f"Bearer {token}",
                                           "content-type": "application/json;charset=UTF-8",
                                       }) as response:
                    return await response.json()
        except Exception as e:
            return str(e)
    async def invite_clan(self, token, short_id):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"https://api.{self.url}/api/clans/invite",
                                        headers={
                                            "accept": "application/json, text/plain, */*",
                                            "authorization": f"Bearer {token}",
                                            "content-type": "application/json;charset=UTF-8",
                                        },
                                        json={"shortId": short_id}) as response:
                    status = response.status
                    try:
                        json_response = await response.json()
                        if json_response:
                            return json_response
                        else:
                            return status
                    except:
                        return status
        except Exception as e:
            return str(e)
    async def get_my_clan(self, token):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.{self.url}/api/clans/mine",
                                    headers={
                                        "accept": "application/json, text/plain, */*",
                                        "authorization": f"Bearer {token}",
                                        "content-type": "application/json;charset=UTF-8",
                                    }) as response:
                    return await response.json()
        except Exception as e:
            return str(e)
    async def get_character_render(self, skinname):
        """
        Retrieves the character render URL from the website.

        Args:
            skinname: The name of the skin.

        Returns:
            The character render URL, or None if not found.
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://{self.url}"
                async with session.get(url) as response:
                    html = await response.text()

                js_file_regex = r"\/assets\/js\/chunk-.{1,10}\..{1,10}\.js"
                js_file_matches = re.findall(js_file_regex, html)

                for item in js_file_matches:
                    url = f"https://{self.url}{item}"
                    async with session.get(url) as js_chunk_file_response:
                        js_chunk_file = await js_chunk_file_response.text()

                    if "Kod" in js_chunk_file and "assets/img/render" in js_chunk_file:
                        try:
                            charsearching = (
                                js_chunk_file.split(f'"./{skinname}/render.png":')[1]
                                .split('",')[0]
                                .replace('"', "")
                                .replace(" ", "")
                            )
                            copy_of_the_chunk_file = js_chunk_file
                            render_url_finder = copy_of_the_chunk_file.split(
                                charsearching + ":"
                            )
                            render_url_finder = render_url_finder[1]
                            if render_url_finder is None:
                                render_url_finder = copy_of_the_chunk_file.split(
                                    charsearching + '":'
                                )
                                render_url_finder = render_url_finder[1]

                            render_url_finder = render_url_finder.split("},")[0]
                            render_url_finder = render_url_finder.split("exports")[1]

                            if "data:image/" in render_url_finder and "base64" in render_url_finder:
                                # Base64
                                base64_render_url_finder = render_url_finder.split('"')[1]
                                return base64_render_url_finder
                            else:
                                # Normal
                                regex_render_url = r'"assets\/img\/render\.[A-Za-z0-9]{0,20}\.png"'
                                url_render_url_finder = re.findall(
                                    regex_render_url, render_url_finder
                                )[0]
                                url_render_url_finder = (
                                    url_render_url_finder.replace('"', "").replace(" ", "")
                                )
                                return f"https://{self.url}/{url_render_url_finder}"
                        except Exception:
                            pass
            return None
        except Exception as e:
            return e
    
    async def pricebvl(self, skinname):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://opensheet.elk.sh/1tzHjKpu2gYlHoCePjp6bFbKBGvZpwDjiRzT9ZUfNwbY/Alphabetical") as response:
                    req = await response.json()
    
            found = False
            value = 0
            skinname = skinname.lower()
    
            if isinstance(req, list):
                for listitem in req:
                    if not found and listitem and "Skin Name" in listitem and "Price" in listitem:
                        if listitem["Skin Name"].lower() == skinname:
                            found = True
                            value = float(listitem["Price"].split(" ")[0].split("?")[0].replace(",", "").replace(".", ""))
    
            if math.isnan(value):
                value = 0
    
            return value
        except Exception as e:
            return e
    
    async def priceyzzzmtz(self, skinname):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://opensheet.elk.sh/1VqX9kwJx0WlHWKCJNGyIQe33APdUSXz0hEFk6x2-3bU/Sorted+View") as response:
                    req = await response.json()
    
            found = False
            value = 0
            skinname = skinname.lower()
    
            if isinstance(req, list):
                for listitem in req:
                    if not found and listitem and "Name" in listitem and "Base Value" in listitem:
                        if listitem["Name"].lower() == skinname:
                            found = True
                            value = float(listitem["Base Value"].split(" ")[0].split("?")[0].replace(",", "").replace(".", ""))
    
            if math.isnan(value):
                value = 0
    
            return value
        except Exception as e:
            return e

    async def pricecustom(self, skinname, namefield, pricefield, opensheeturl):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(opensheeturl) as response:
                    req = await response.json()

            found = False
            value = 0
            skinname = skinname.lower()

            if isinstance(req, list):
                for listitem in req:
                    if not found and listitem and namefield in listitem and pricefield in listitem:
                        if listitem[namefield].lower() == skinname:
                            found = True
                            value = float(listitem[pricefield].split(" ")[0].split("?")[0].replace(",", "").replace(".", ""))

            if math.isnan(value):
                value = 0

            return value
        except Exception as e:
            return e


    async def getClan(self, name):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.{self.url}/api/clans/{name}", headers={
                    "accept": "application/json, text/plain, */*",
                    "content-type": "application/json;charset=UTF-8"
                }) as response:
                    return await response.json()
        except Exception as e:
            return e


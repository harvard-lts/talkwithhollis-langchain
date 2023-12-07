import os
import asyncio
from datetime import datetime
from app.config import settings
import httpx
import json

from .file import FileUtils

class LibCalUtils():
    def __init__(self):
        self.file_utils = FileUtils()

    async def get_library_hours(self):
        # Get cached hours
        cached_library_hours_json = await self.file_utils.get_and_init_library_cache_file()
        if cached_library_hours_json is None:
            print('Error: Unable to get library hours. cached_library_hours_json is None')
            return None
        
        time_now = datetime.now()
        cached_time = datetime.strptime(cached_library_hours_json['timestamp'], "%m/%d/%Y, %H:%M:%S")
        difference = time_now - cached_time

        if difference.seconds > settings.libcal_refresh_time or len(cached_library_hours_json['libraries']) == 0:
            # Do refresh
            libcal_results = await self.get_refreshed_library_hours()
            formatted_hours = await self.format_hours(libcal_results)
            cached_library_hours_json['libraries'] = formatted_hours
            cached_library_hours_json['timestamp'] = time_now.strftime("%m/%d/%Y, %H:%M:%S")
            await self.file_utils.write_cached_library_hours_json(cached_library_hours_json)
            return cached_library_hours_json['libraries']
        else:
            # Do not do the refresh
            return cached_library_hours_json['libraries']
      
    async def format_hours(self, libcal_results):
        formatted_hours = {}
        for result in libcal_results:
            library_code = result[0]

            print(result)
            try:
                date = result[1][0]["dates"][list(result[1][0]["dates"].keys())[0]]
                status = date.get("status")
                if status == "closed":
                    listing = "Closed"
                elif status == "24hours":
                    listing = "Open 24 Hours"
                elif status == "open":
                    listing = "Open"
                    if "hours" in date:
                        hours = date["hours"][0]
                        listing += " from " + hours["from"] + " to " + hours["to"]
                else:
                    listing = "Operating Hours unknown, please check library website"
            except:
                # This is to catch data out of the expected format, in particular the Wolbach Library, which contains an empty list instead of a formatted dates object
                listing = "Operating Hours unknown, please check library website"

            formatted_hours[library_code] = listing
        
        return formatted_hours
        
    
    async def get_refreshed_library_hours(self):
        libraries = await self.file_utils.open_json_file('app/schemas/library_libcal_codes.json')

        libcal_token = await self.get_libcal_token()

        result = await self.get_all_library_hours(libraries, libcal_token)
        return result

    async def get_all_library_hours(self, libraries, libcal_token):
        tasks = []
        async with httpx.AsyncClient() as client:
            for library in libraries:
                tasks.append(self.get_library_hours_by_code(client, library, libraries[library], libcal_token))
            responses = await asyncio.gather(*tasks)
            return responses

    async def get_library_hours_by_code(self, client, library, libcal_library_id, access_token):
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.libcal_hours_api_route + str(libcal_library_id), headers={"Authorization": "Bearer " + access_token})
        return [library, response.json()]

    async def get_libcal_token(self):
        post_body = json.dumps({
            "client_id": settings.libcal_client_id,
            "client_secret": settings.libcal_client_secret,
            "grant_type": "client_credentials"
        })
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.libcal_token_api_route, content=post_body, headers={"Content-Type": "application/json"})
        access_token = response.json().get('access_token')
        return access_token

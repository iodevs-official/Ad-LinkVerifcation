import aiohttp
import logging
from config import modiji_url, modiji_api


async def shorten_url(link: str) -> str:
    api_url = f'https://{modiji_url}/api'
    params = {
        'api': modiji_api,
        'url': link,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, raise_for_status=True, ssl=False) as response:
                try:
                    data = await response.json()
                    if data.get("status") == "success":
                        return data['shortenedUrl']
                    else:
                        print.error(f"API Error: {data.get('message', 'Unknown error')}")
                        return f'https://{url}/api?api={api_key}&url={link}'
                except aiohttp.ContentTypeError:
                    print.error("Failed to parse JSON response.")
                    return f'https://{url}/api?api={api_key}&url={link}'
    except aiohttp.ClientError as e:
        print.error(f"HTTP request failed: {e}")
        return f'https://{url}/api?api={api_key}&url={link}'
    except Exception as e:
        print.error(f"An unexpected error occurred: {e}")
        return f'https://{url}/api?api={api_key}&url={link}'

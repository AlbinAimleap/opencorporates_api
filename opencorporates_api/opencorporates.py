from bs4 import BeautifulSoup
from typing import List, Dict
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import os


class CompanyDataScraper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://opencorporates.com"
        self.api_endpoint = "https://api.zyte.com/v1/extract"
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_html(self, url: str) -> BeautifulSoup:
        async with self.session.post(
            self.api_endpoint,
            auth=aiohttp.BasicAuth(self.api_key, ""),
            json={
                "url": url,
                "browserHtml": True,
                "actions": [
                    {"action": "waitForTimeout", "timeout": 2}
                ]
            }
        ) as response:
            data = await response.json()
            browser_html: str = data.get("browserHtml")
            return await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: BeautifulSoup(browser_html, "html.parser")
            )

    def get_company_links(self, soup: BeautifulSoup) -> List[str]:
        return [
            f"{self.base_url}{link['href']}" 
            for link in soup.findAll('a', class_=lambda c: 'company_search_result' in c.split() if c else False)
        ]

    def extract_company_data(self, soup: BeautifulSoup, link: str) -> Dict:
        company_name = soup.find('h1').text.strip()
        company_info = {'Company Link': link, 'Company Name': company_name}

        attributes_div = soup.find('div', {'id': 'attributes'})
        if attributes_div:
            for dt, dd in zip(attributes_div.find_all('dt'), attributes_div.find_all('dd')):
                company_info[dt.text.strip()] = dd.text.strip()

        return company_info

    async def search_companies(self, query: str, jurisdiction: str = None) -> List[Dict]:
        formatted_query = "+".join(query.split())
        search_url = f'{self.base_url}/companies?utf8=%E2%9C%93&q={formatted_query}&jurisdiction_code={jurisdiction}&type=companies'
        
        search_results = await self.fetch_html(search_url)
        company_links = self.get_company_links(search_results)
        tasks = [self.fetch_html(link) for link in company_links]
        company_pages = await asyncio.gather(*tasks)
        
        extract_partial = partial(self.extract_company_data)
        company_data = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            lambda: [extract_partial(page, link) for page, link in zip(company_pages, company_links)]
        )
        
        return company_data


async def search(query: str, jurisdiction: str = None) -> List[Dict]:
    jurisdiction = jurisdiction or ''
    api_key = os.getenv("ZYTE_API_KEY")
    async with CompanyDataScraper(api_key) as scraper:
        results = await scraper.search_companies(query, jurisdiction)
        yield results


if __name__ == "__main__":
    asyncio.run(search('real estate'))
# copy and modify from:
# langchain_community.document_loaders.async_html.py(version:0.0.34)

import asyncio
import logging
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, List, Optional, Union, cast

import aiohttp
import requests
from langchain_core.documents import Document

from langchain_community.document_loaders.base import BaseLoader

logger = logging.getLogger(__name__)

default_header_template = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*"
    ";q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://cn.bing.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "cookies": "_EDGE_V=1; MUID=20AC24E325F16DF806F430AF24B26C89; MUIDB=20AC24E325F16DF806F430AF24B26C89; SRCHD=AF=NOFORM; SRCHUID=V=2&GUID=3E60E76FA3A34529B5BF8C4BFA8BABDC&dmnchg=1; MicrosoftApplicationsTelemetryDeviceId=d430c583-87cf-4349-8aef-d4bfbef242f8; MUIDV=NU=1; MMCASM=ID=4C9ED7BF6DDD42A88D9AD109E3C48DAC; TRBDG=FIMPR=1; _TTSS_IN=hist=WyJlbiIsImF1dG8tZGV0ZWN0Il0=&isADRU=0; _TTSS_OUT=hist=WyJ6aC1IYW5zIl0=; ttaNewFeature=tonetranslation; _UR=QS=0&TQS=0; ANIMIA=FRE=1; mapc=rm=0; NAP=V=1.9&E=1d61&C=1G5awyJ_kn5sdiYSERsi4FHixTLh4YutLIb0OmC8kFbsyRmW-Z1wLQ&W=1; _tarLang=default=zh-Hans&newFeature=tonetranslation; ABDEF=V=13&ABDV=13&MRNB=1715611500413&MRB=0; _EDGE_S=SID=16AF556628EC60700BE94119298A61B2; USRLOC=HS=1&ELOC=LAT=39.08474349975586|LON=117.20085144042969|N=%E5%A4%A9%E6%B4%A5%EF%BC%8C%E5%A4%A9%E6%B4%A5%E5%B8%82|ELT=1|; _Rwho=u=d&ts=2024-05-14; _SS=SID=16AF556628EC60700BE94119298A61B2&R=201&RB=201&GB=0&RG=0&RP=201; ipv6=hit=1715696137864; _C_ETH=1; _HPVN=CS=eyJQbiI6eyJDbiI6NDUsIlN0IjowLCJRcyI6MCwiUHJvZCI6IlAifSwiU2MiOnsiQ24iOjQ1LCJTdCI6MCwiUXMiOjAsIlByb2QiOiJIIn0sIlF6Ijp7IkNuIjo0NSwiU3QiOjAsIlFzIjowLCJQcm9kIjoiVCJ9LCJBcCI6dHJ1ZSwiTXV0ZSI6dHJ1ZSwiTGFkIjoiMjAyNC0wNS0xNFQwMDowMDowMFoiLCJJb3RkIjowLCJHd2IiOjAsIlRucyI6MCwiRGZ0IjpudWxsLCJNdnMiOjAsIkZsdCI6MCwiSW1wIjo2MTUsIlRvYm4iOjB9; SRCHHPGUSR=SRCHLANG=zh-Hans&BRW=XW&BRH=M&CW=1911&CH=964&SCW=1911&SCH=965&DPR=3.1&UTC=480&DM=0&PV=6.5.0&WTS=63850591402&HV=1715692974&BZA=0&PRVCW=812&PRVCH=964&IG=F70D7E585C844A7F84CAF3CDDE754F56; ai_session=3T0Uq3l0HPx3MQMWvdD2rT|1715692520861|1715692977222; WLS=C=&N=; SRCHUSR=DOB=20240324&T=1715692517000&TPC=1715683241000; SNRHOP=I=&TS=",
}


def _build_metadata(soup: Any, url: str) -> dict:
    """Build metadata from BeautifulSoup output."""
    metadata = {"source": url}
    if title := soup.find("title"):
        metadata["title"] = title.get_text()
    if description := soup.find("meta", attrs={"name": "description"}):
        metadata["description"] = description.get("content", "No description found.")
    if html := soup.find("html"):
        metadata["language"] = html.get("lang", "No language found.")
    return metadata


class AsyncHtmlLoader(BaseLoader):
    """Load `HTML` asynchronously."""

    def __init__(
        self,
        web_path: Union[str, List[str]],
        header_template: Optional[dict] = None,
        verify_ssl: Optional[bool] = True,
        proxies: Optional[dict] = None,
        autoset_encoding: bool = True,
        encoding: Optional[str] = None,
        default_parser: str = "html.parser",
        requests_per_second: int = 2,
        requests_kwargs: Optional[Dict[str, Any]] = None,
        raise_for_status: bool = False,
        ignore_load_errors: bool = False,
    ):
        """Initialize with a webpage path."""

        # TODO: Deprecate web_path in favor of web_paths, and remove this
        # left like this because there are a number of loaders that expect single
        # urls
        if isinstance(web_path, str):
            self.web_paths = [web_path]
        elif isinstance(web_path, List):
            self.web_paths = web_path

        headers = header_template or default_header_template
        if not headers.get("User-Agent"):
            try:
                from fake_useragent import UserAgent

                headers["User-Agent"] = UserAgent().random
            except ImportError:
                logger.info(
                    "fake_useragent not found, using default user agent."
                    "To get a realistic header for requests, "
                    "`pip install fake_useragent`."
                )

        self.session = requests.Session()
        self.session.headers = dict(headers)
        self.session.verify = verify_ssl

        if proxies:
            self.session.proxies.update(proxies)

        self.requests_per_second = requests_per_second
        self.default_parser = default_parser
        self.requests_kwargs = requests_kwargs or {}
        self.raise_for_status = raise_for_status
        self.autoset_encoding = autoset_encoding
        self.encoding = encoding
        self.ignore_load_errors = ignore_load_errors

    def _fetch_valid_connection_docs(self, url: str) -> Any:
        if self.ignore_load_errors:
            try:
                return self.session.get(url, **self.requests_kwargs)
            except Exception as e:
                warnings.warn(str(e))
                return None

        return self.session.get(url, **self.requests_kwargs)

    @staticmethod
    def _check_parser(parser: str) -> None:
        """Check that parser is valid for bs4."""
        valid_parsers = ["html.parser", "lxml", "xml", "lxml-xml", "html5lib"]
        if parser not in valid_parsers:
            raise ValueError(
                "`parser` must be one of " + ", ".join(valid_parsers) + "."
            )

    def _scrape(
        self,
        url: str,
        parser: Union[str, None] = None,
        bs_kwargs: Optional[dict] = None,
    ) -> Any:
        from bs4 import BeautifulSoup

        if parser is None:
            if url.endswith(".xml"):
                parser = "xml"
            else:
                parser = self.default_parser

        self._check_parser(parser)

        html_doc = self._fetch_valid_connection_docs(url)
        if not getattr(html_doc, "ok", False):
            return None

        if self.raise_for_status:
            html_doc.raise_for_status()

        if self.encoding is not None:
            html_doc.encoding = self.encoding
        elif self.autoset_encoding:
            html_doc.encoding = html_doc.apparent_encoding
        return BeautifulSoup(html_doc.text, parser, **(bs_kwargs or {}))

    async def _fetch(
        self, url: str, retries: int = 1, cooldown: int = 2, backoff: float = 1.5
    ) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                for i in range(retries):
                    try:
                        async with session.get(
                            url,
                            headers=self.session.headers,
                            ssl=None if self.session.verify else False,
                        ) as response:
                            try:
                                text = await response.text()
                            except UnicodeDecodeError:
                                logger.error(f"Failed to decode content from {url}")
                                text = ""
                            return text
                    except aiohttp.ClientConnectionError as e:
                        if i == retries - 1 and self.ignore_load_errors:
                            logger.warning(
                                f"Error fetching {url} after {retries} retries."
                            )
                            return ""
                        elif i == retries - 1:
                            raise
                        else:
                            logger.warning(
                                f"Error fetching {url} with attempt "
                                f"{i + 1}/{retries}: {e}. Retrying..."
                            )
                            await asyncio.sleep(cooldown * backoff**i)
        except Exception as e:
            return ""
        # raise ValueError("retry count exceeded")

    async def _fetch_with_rate_limit(
        self, url: str, semaphore: asyncio.Semaphore
    ) -> str:
        async with semaphore:
            return await self._fetch(url)

    async def fetch_all(self, urls: List[str]) -> Any:
        """Fetch all urls concurrently with rate limiting."""
        semaphore = asyncio.Semaphore(self.requests_per_second)
        tasks = []
        for url in urls:
            task = asyncio.ensure_future(self._fetch_with_rate_limit(url, semaphore))
            tasks.append(task)
        try:
            from tqdm.asyncio import tqdm_asyncio

            return await tqdm_asyncio.gather(
                *tasks, desc="Fetching pages", ascii=True, mininterval=1
            )
        except ImportError:
            warnings.warn("For better logging of progress, `pip install tqdm`")
            return await asyncio.gather(*tasks)

    def lazy_load(self) -> Iterator[Document]:
        """Lazy load text from the url(s) in web_path."""
        for doc in self.load():
            yield doc

    def load(self) -> List[Document]:
        """Load text from the url(s) in web_path."""

        try:
            # Raises RuntimeError if there is no current event loop.
            asyncio.get_running_loop()
            # If there is a current event loop, we need to run the async code
            # in a separate loop, in a separate thread.
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, self.fetch_all(self.web_paths))
                results = future.result()
        except RuntimeError:
            results = asyncio.run(self.fetch_all(self.web_paths))
        docs = []
        for i, text in enumerate(cast(List[str], results)):
            soup = self._scrape(self.web_paths[i])
            if not soup:
                continue
            metadata = _build_metadata(soup, self.web_paths[i])
            docs.append(Document(page_content=text, metadata=metadata))

        return docs

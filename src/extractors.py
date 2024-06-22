from abc import ABC, abstractmethod
from typing import Dict, Any
from web_browser import WebBrowser
from handlers import FormUtils


class MetadataExtractor(ABC):
    @abstractmethod
    async def extract(self, browser: "WebBrowser") -> Dict[str, Any]:
        pass


class FormMetadataExtractor(MetadataExtractor):
    async def extract(self, browser: "WebBrowser") -> Dict[str, Any]:
        forms = await FormUtils.get_forms(browser)
        return {"forms": forms}


class H1MetadataExtractor(MetadataExtractor):
    async def extract(self, browser: "WebBrowser") -> Dict[str, Any]:
        h1_elements = await browser.page.query_selector_all("h1")
        h1_data = [
            {
                "id": await h1.get_attribute("id"),
                "class": await h1.get_attribute("class"),
                "inner_text": await h1.inner_text(),
            }
            for h1 in h1_elements
        ]
        return {"h1": h1_data}


class H2MetadataExtractor(MetadataExtractor):
    async def extract(self, browser: "WebBrowser") -> Dict[str, Any]:
        h2_elements = await browser.page.query_selector_all("h2")
        h2_data = [
            {
                "id": await h2.get_attribute("id"),
                "class": await h2.get_attribute("class"),
                "inner_text": await h2.inner_text(),
            }
            for h2 in h2_elements
        ]
        return {"h2": h2_data}


class LinksMetadataExtractor(MetadataExtractor):
    async def extract(self, browser: "WebBrowser") -> Dict[str, Any]:
        link_elements = await browser.page.query_selector_all("a")
        links_data = [
            {
                "href": await link.get_attribute("href"),
                "inner_text": await link.inner_text(),
            }
            for link in link_elements
        ]
        return {"links": links_data}


class PageTitleExtractor(MetadataExtractor):
    async def extract(self, browser: "WebBrowser") -> Dict[str, Any]:
        title_element = await browser.page.query_selector("title")
        title_text = await title_element.inner_text() if title_element else ""
        return {"title": title_text}


class ImagesMetadataExtractor(MetadataExtractor):
    async def extract(self, browser: "WebBrowser") -> Dict[str, Any]:
        img_elements = await browser.page.query_selector_all("img")
        images_data = [
            {
                "src": await img.get_attribute("src"),
                "alt": await img.get_attribute("alt"),
            }
            for img in img_elements
        ]
        return {"images": images_data}


class MetaDescriptionExtractor(MetadataExtractor):
    async def extract(self, browser: "WebBrowser") -> Dict[str, Any]:
        meta_description = await browser.page.query_selector("meta[name='description']")
        description_content = (
            await meta_description.get_attribute("content") if meta_description else ""
        )
        return {"meta_description": description_content}

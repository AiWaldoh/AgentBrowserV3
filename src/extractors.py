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


class ButtonMetadataExtractor(MetadataExtractor):
    async def extract(self, browser: "WebBrowser") -> Dict[str, Any]:
        button_elements = await browser.page.query_selector_all("button")
        unique_buttons: Dict[str, Dict[str, Any]] = {}

        for button in button_elements:
            button_id = await button.get_attribute("id") or ""
            button_class = await button.get_attribute("class") or ""
            key = f"{button_id}_{button_class}"

            if key not in unique_buttons:
                button_data = {}

                if button_id:
                    button_data["id"] = button_id
                if button_class:
                    button_data["class"] = button_class

                button_type = await button.get_attribute("type")
                if button_type:
                    button_data["type"] = button_type

                button_name = await button.get_attribute("name")
                if button_name:
                    button_data["name"] = button_name

                inner_text = await button.inner_text()
                if inner_text:
                    button_data["inner_text"] = inner_text

                if button_data:  # Only add if we have any non-empty attributes
                    unique_buttons[key] = button_data

        buttons_data = list(unique_buttons.values())
        return {"buttons": buttons_data}


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

from abc import ABC, abstractmethod
import json
from typing import Dict, Any
import os
from datetime import datetime
from web_browser import WebBrowser


class DependenciesContainer:
    def __init__(self, **dependencies):
        self.dependencies = dependencies

    def get(self, key, default=None):
        """Retrieve a dependency by key."""
        return self.dependencies.get(key, default)

    def set(self, key, value):
        """Set a dependency."""
        self.dependencies[key] = value

    def remove(self, key):
        """Remove a dependency."""
        if key in self.dependencies:
            del self.dependencies[key]


class AITaskRegistry:
    _instance = None
    _registry = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, task_name, command):
        cls._registry[task_name] = command

    @classmethod
    def get_command(cls, task_name):
        return cls._registry.get(task_name)


class TaskExecutor:

    @staticmethod
    def execute_task(task_name, arguments, dependencies_container):
        task = AITaskRegistry.get_command(task_name)
        if task:
            return task.execute(json.loads(arguments), dependencies_container)
        else:
            print(f"Task '{task_name}' not found.")
            return None


class Task(ABC):
    @abstractmethod
    def execute(self, arguments, dependencies_container):
        pass


class ScreenshotUtils:
    @staticmethod
    def generate_screenshot_path(folder_name: str = "screenshots") -> str:
        os.makedirs(folder_name, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"{folder_name}/screenshot_{timestamp}.png"
        return file_name


class TakeScreenshotTask(Task):
    async def execute(self, arguments: Dict[str, Any], dependencies_container) -> str:
        browser = dependencies_container.get("web_browser")

        if browser:
            file_name = ScreenshotUtils.generate_screenshot_path()
            await browser.take_screenshot(file_name)
            print(f"Screenshot captured and saved as: {file_name}")
            return file_name
        else:
            raise ValueError("Web browser dependency is missing")


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


class MetadataManager:
    def __init__(self, extractors: list[MetadataExtractor]):
        self.extractors = extractors

    async def extract_all(self, browser: "WebBrowser") -> Dict[str, Any]:
        metadata = {}
        for extractor in self.extractors:
            print(
                "Extracting metadata using extractor: " + extractor.__class__.__name__
            )
            metadata.update(await extractor.extract(browser))
        return metadata


class GoToPageTask(Task):
    def __init__(self):
        # Initialize MetadataManager with all the extractors you need
        self.metadata_manager = MetadataManager(
            [
                FormMetadataExtractor(),
                H1MetadataExtractor(),
                H2MetadataExtractor(),
                LinksMetadataExtractor(),
                PageTitleExtractor(),
                ImagesMetadataExtractor(),
                MetaDescriptionExtractor(),
            ]
        )

    async def execute(
        self, arguments: Dict[str, Any], dependencies_container: "DependenciesContainer"
    ) -> Dict[str, Any]:
        browser: WebBrowser = dependencies_container.get("web_browser")
        if browser:
            await browser.navigate_to(arguments["url"])
            print("Page loaded successfully.")
            metadata = await self.metadata_manager.extract_all(browser)
            print("Metadata extracted successfully.")
            formatted_response = CLIResponseFormatter().format(metadata)
            print("Response formatted successfully.")
            if formatted_response:
                pass
                # print(formatted_response)
            else:
                print("No metadata found.")
            return metadata
        else:
            raise ValueError("Web browser dependency is missing")


class FormElementHandler(ABC):
    @abstractmethod
    async def handle(self, element) -> Dict[str, Any]:
        pass


class InputFieldHandler(FormElementHandler):
    async def handle(self, element) -> Dict[str, Any]:
        return {
            "type": await element.get_attribute("type"),
            "name": await element.get_attribute("name"),
            "id": await element.get_attribute("id"),
            "class": await element.get_attribute("class"),
            "placeholder": await element.get_attribute("placeholder"),
            "label": await self.get_associated_label(element),
        }

    async def get_associated_label(self, element):
        label_element = await element.query_selector(
            "xpath=preceding-sibling::label[1]"
        )
        if label_element:
            return await label_element.inner_text()
        return None


class ButtonHandler(FormElementHandler):
    async def handle(self, element) -> Dict[str, Any]:
        return {
            "type": await element.get_attribute("type"),
            "name": await element.get_attribute("name"),
            "id": await element.get_attribute("id"),
            "class": await element.get_attribute("class"),
            "value": await element.get_attribute("value"),
            "label": await self.get_button_label(element),
        }

    async def get_button_label(self, button):
        if await button.get_attribute("value"):
            return await button.get_attribute("value")
        return await button.inner_text()


class SelectHandler(FormElementHandler):
    async def handle(self, element) -> Dict[str, Any]:
        return {
            "name": await element.get_attribute("name"),
            "id": await element.get_attribute("id"),
            "class": await element.get_attribute("class"),
            "label": await self.get_associated_label(element),
            "options": await self.get_select_options(element),
        }

    async def get_associated_label(self, element):
        label_element = await element.query_selector(
            "xpath=preceding-sibling::label[1]"
        )
        if label_element:
            return await label_element.inner_text()
        return None

    async def get_select_options(self, select):
        options = await select.query_selector_all("option")
        return [await option.get_attribute("value") for option in options]


element_handlers = {
    "input": InputFieldHandler(),
    "button": ButtonHandler(),
    "select": SelectHandler(),
}


class FormUtils:
    @staticmethod
    async def get_forms(browser):
        forms = []
        page = browser.page
        await page.wait_for_selector("form", state="hidden")
        elements = await page.query_selector_all("form")
        for element in elements:
            form_data = {
                "id": await element.get_attribute("id"),
                "name": await element.get_attribute("name"),
                "action": await element.get_attribute("action"),
                "method": await element.get_attribute("method"),
                "elements": [],
            }

            for element_type, handler in element_handlers.items():
                sub_elements = await element.query_selector_all(element_type)
                for sub_element in sub_elements:
                    element_data = await handler.handle(sub_element)
                    form_data["elements"].append(element_data)

            forms.append(form_data)

        return forms


class JSONResponseFormatter:
    def format(self, metadata: Dict[str, Any]) -> str:
        import json

        return json.dumps(metadata, indent=2)


class FormParser:
    @staticmethod
    def parse_forms(forms):
        num_forms = len(forms)
        feedback = f"Website loaded successfully. It has {num_forms} form(s).\n\n"

        for index, form in enumerate(forms, start=1):
            form_id = form.get("id", "N/A")
            form_name = form.get("name", "N/A")
            form_action = form.get("action", "N/A")
            form_method = form.get("method", "GET")
            num_elements = len(form["elements"])

            feedback += f"Form {index}:\n"
            feedback += f"  ID: {form_id}\n"
            feedback += f"  Name: {form_name}\n"
            feedback += f"  Action: {form_action}\n"
            feedback += f"  Method: {form_method}\n"
            feedback += f"  Number of Elements: {num_elements}\n"

            feedback += "  Elements:\n"
            for element in form["elements"]:
                element_type = element.get("type", "N/A")
                element_name = element.get("name", "N/A")
                element_id = element.get("id", "N/A")
                element_class = element.get("class", "N/A")
                element_label = element.get("label", "N/A")

                feedback += f"    - Type: {element_type}\n"
                feedback += f"      Name: {element_name}\n"
                feedback += f"      ID: {element_id}\n"
                feedback += f"      Class: {element_class}\n"
                feedback += f"      Label: {element_label}\n"

                if element_type == "select":
                    options = element.get("options", [])
                    feedback += f"      Options: {', '.join(options)}\n"

            feedback += "\n"

        return feedback


class CLIResponseFormatter:
    def format(self, metadata: Dict[str, Any]) -> str:
        response = "Website metadata extracted successfully.\n\n"

        for meta_type, details in metadata.items():
            response += f"{meta_type.capitalize()}:\n"
            if isinstance(details, list):
                for detail in details:
                    response += (
                        "  - "
                        + "\n      ".join(f"{k}: {v}" for k, v in detail.items())
                        + "\n"
                    )
            else:
                response += "  - " + str(details) + "\n"
            response += "\n"

        return "\033[94m" + response + "\033[0m"


# class GoToPageTask(Task):
#     async def execute(self, arguments, dependencies_container):
#         browser = dependencies_container.get("web_browser")
#         if browser:
#             await browser.navigate_to(arguments["url"])
#             print("Page loaded successfully.")

#             # manipulate page
#             page = browser.page
#             forms = await FormUtils.get_forms(page)
#             parsed_forms = FormParser.parse_forms(forms)
#             formatted_response = CLIResponseFormatter().format(parsed_forms)
#             # file_name = ScreenshotUtils.generate_screenshot_path()
#             # await browser.take_screenshot(file_name)
#             # print(f"Screenshot captured and saved as: {file_name}")

#             print(formatted_response)

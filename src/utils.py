import os
from datetime import datetime
from abc import ABC, abstractmethod
import json
from typing import Dict, Any
from web_browser import WebBrowser
from http_api_async import ChatAPIService
from typing import List, Dict, Any
from extractors import MetadataExtractor
from typing import List, Dict, Any
import asyncio


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


class ScreenshotUtils:
    @staticmethod
    def generate_screenshot_path(folder_name: str = "screenshots") -> str:
        os.makedirs(folder_name, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"{folder_name}/screenshot_{timestamp}.png"
        return file_name


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


class FieldInteractor:
    def __init__(self, browser):
        self.browser = browser

    async def fill_text_input(self, selector, value):
        element = await self._get_element(selector)
        await element.fill(value)
        print(f"Filled input {selector} with value {value}")

    async def fill_text_area(self, selector, value):
        element = await self._get_element(selector)
        await element.fill(value)
        print(f"Filled textarea {selector} with value {value}")

    async def select_option(self, selector, value):
        element = await self._get_element(selector)
        await element.select_option(value)
        print(f"Selected option {value} in {selector}")

    async def fill_checkbox_or_radio(self, selector, value):
        if value:
            await self._force_click(selector)
            print(f"Checked {selector}")
        else:
            element = await self._get_element(selector)
            input_type = await element.get_attribute("type")
            if input_type == "checkbox":
                await self._force_click(selector)
                print(f"Unchecked {selector}")

    async def _force_click(self, selector):
        try:
            await self.browser.page.evaluate(
                f"""
                (selector) => {{
                    const element = document.querySelector(selector);
                    if (element) {{
                        element.click();
                    }}
                }}
                """,
                selector,
            )
            print(f"Forced click on {selector}")
        except Exception as e:
            print(f"Error forcing click on {selector}: {str(e)}")
            raise

    async def _get_element(self, selector):
        element = await self.browser.page.query_selector(selector)
        if element is None:
            raise ValueError(f"Element with selector {selector} not found")
        return element


class SubmitInteractor:
    def __init__(self, browser):
        self.browser = browser

    async def submit_form(self, submit_button_selector):
        try:
            await asyncio.sleep(1)  # Optional delay
            submit_button = await self.browser.page.query_selector(
                submit_button_selector
            )
            if submit_button:
                await submit_button.click()
                print("Form submitted successfully by clicking the submit button.")
            else:
                print(f"Submit button not found with selector {submit_button_selector}")
        except Exception as e:
            print(f"Error submitting form: {str(e)}")
            raise


class FormInteractor:
    def __init__(self, browser):
        self.field_interactor = FieldInteractor(browser)
        self.submit_interactor = SubmitInteractor(browser)

    async def fill_form_fields(self, field_mappings: List[Dict[str, Any]]):
        print(f"Filling form fields with {field_mappings}")
        submit_selector = None
        for mapping in field_mappings:
            selector = mapping.get("field_selector")
            value = mapping.get("value")
            reason = mapping.get("reason")

            # Identify the submit button selector
            if reason and "submit" in reason.lower():
                submit_selector = selector
                continue

            if selector and value is not None:
                await self.fill_field(selector, value)

        # Submit the form if the submit button selector is found
        if submit_selector:
            await self.submit_interactor.submit_form(submit_selector)
        else:
            print("No submit button selector found in the API response")

    async def fill_field(self, selector, value):
        try:
            element = await self.field_interactor._get_element(selector)
            tag_name = await element.evaluate("(element) => element.tagName")

            if tag_name == "INPUT":
                input_type = await element.get_attribute("type")
                if input_type in ["checkbox", "radio"]:
                    await self.field_interactor.fill_checkbox_or_radio(selector, value)
                else:
                    await self.field_interactor.fill_text_input(selector, value)
            elif tag_name == "TEXTAREA":
                await self.field_interactor.fill_text_area(selector, value)
            elif tag_name == "SELECT":
                await self.field_interactor.select_option(selector, value)
            else:
                print(f"Unhandled form element {tag_name} for selector {selector}")

            await asyncio.sleep(
                0.5
            )  # Allow time for any client-side validation or async operations
        except Exception as e:
            print(f"Error filling field {selector}: {str(e)}")
            raise

import os
from datetime import datetime
from abc import ABC, abstractmethod
import json
from typing import Dict, Any
from web_browser import WebBrowser
import asyncio
from http_api_async import ChatAPIService
from typing import List, Dict, Any
from extractors import MetadataExtractor


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


class FormInteractor:
    def __init__(self, browser):
        self.browser = browser

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
                await self._fill_field(selector, value)

        # Submit the form if the submit button selector is found
        if submit_selector:
            await asyncio.sleep(1)  # Optional delay
            await self.submit_form(submit_selector)
        else:
            print("No submit button selector found in the API response")

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

    async def _fill_field(self, selector, value):
        try:
            element = await self.browser.page.query_selector(selector)
            if element is None:
                print(f"Element with selector {selector} not found")
                return

            tag_name = await element.evaluate("(element) => element.tagName")

            if tag_name == "INPUT":
                input_type = await element.get_attribute("type")
                if input_type in ["checkbox", "radio"]:
                    if value:
                        await self._force_click(selector)
                        print(f"Set {selector} to checked")
                    else:
                        # Only uncheck if it's a checkbox
                        if input_type == "checkbox":
                            await self._force_click(selector)
                            print(f"Set {selector} to unchecked")
                else:
                    await element.fill(value)
                    print(f"Filled field {selector} with value: {value}")
            elif tag_name == "TEXTAREA":
                await element.fill(value)
                print(f"Filled textarea {selector} with value: {value}")
            elif tag_name == "SELECT":
                await element.select_option(value)
                print(f"Selected option {value} in {selector}")
            else:
                print(f"Unhandled form element {tag_name} for selector {selector}")

            await asyncio.sleep(
                0.5
            )  # Allow time for any client-side validation or async operations
        except Exception as e:
            print(f"Error filling field {selector}: {str(e)}")
            raise

    async def _force_click(self, selector):
        """Force click an element using JavaScript."""
        try:
            await self.browser.page.evaluate(
                f"""
            (selector) => {{
                const element = document.querySelector(selector);
                if (element) {{
                    const rect = element.getBoundingClientRect();
                    element.dispatchEvent(new MouseEvent('mousedown', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: rect.x + rect.width / 2,
                        clientY: rect.y + rect.height / 2
                    }}));
                    element.dispatchEvent(new MouseEvent('mouseup', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: rect.x + rect.width / 2,
                        clientY: rect.y + rect.height / 2
                    }}));
                    element.dispatchEvent(new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: rect.x + rect.width / 2,
                        clientY: rect.y + rect.height / 2
                    }}));
                }}
            }}
            """,
                selector,
            )
            print(f"Forced click on {selector}")
        except Exception as e:
            print(f"Error forcing click on {selector}: {str(e)}")
            raise

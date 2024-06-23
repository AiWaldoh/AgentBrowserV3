from typing import Dict, Any
import os
from web_browser import WebBrowser
from http_api_async import ChatAPIService
from typing import Dict, Any
from utils import (
    ScreenshotUtils,
    Task,
    MetadataManager,
    FormInteractor,
    DependenciesContainer,
)
from extractors import (
    FormMetadataExtractor,
    H1MetadataExtractor,
    H2MetadataExtractor,
    LinksMetadataExtractor,
    PageTitleExtractor,
    ImagesMetadataExtractor,
    MetaDescriptionExtractor,
    ButtonMetadataExtractor,
)

from agentFour import FormParsingAgent


class TakeScreenshotTask(Task):
    async def execute(self, arguments: Dict[str, Any], dependencies_container) -> str:
        browser = dependencies_container.get("web_browser")

        if browser:
            file_name = ScreenshotUtils.generate_screenshot_path()
            await browser.take_screenshot(file_name)
            # print(f"Screenshot captured and saved as: {file_name}")
            return file_name
        else:
            raise ValueError("Web browser dependency is missing")


class InteractWithFormTask(Task):
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
                ButtonMetadataExtractor(),
            ]
        )

    async def execute(
        self, arguments: Dict[str, Any], dependencies_container: DependenciesContainer
    ) -> bool:
        browser = dependencies_container.get("web_browser")
        chat_api_service: ChatAPIService = ChatAPIService(
            os.getenv("OPENAI_API_KEY")
        )  # dependencies_container.get("chat_api_service")

        if not browser:
            print("Web browser dependency is missing")
            return False

        if not chat_api_service:
            print("Chat API service dependency is missing")
            return False

        metadata = await self.metadata_manager.extract_all(browser)
        form_interactor = FormInteractor(browser)
        parsing_agent = FormParsingAgent(chat_api_service)

        user_prompt = arguments.get("user_prompt", "")
        form_data = metadata["forms"]
        buttons_data = metadata["buttons"]

        combined_data = form_data + buttons_data
        print(f"Form data: {combined_data}")
        try:
            field_mappings = await parsing_agent.determine_relevant_form_fields(
                combined_data, user_prompt
            )
            if not field_mappings:
                print("No relevant form fields found.")
                return False
            await form_interactor.fill_form_fields(field_mappings)
            print("Form fields filled successfully")
            return True
        except Exception as e:
            print(f"Error interacting with form: {str(e)}")
            return False


class GoToPageTask(Task):

    async def execute(
        self, arguments: Dict[str, Any], dependencies_container: "DependenciesContainer"
    ) -> Dict[str, Any]:
        browser: WebBrowser = dependencies_container.get("web_browser")
        if browser:
            await browser.navigate_to(arguments["url"])
            print("Page loaded successfully.")
            file_name = ScreenshotUtils.generate_screenshot_path()
            await browser.take_screenshot(file_name)
            print(f"Screenshot captured and saved as: {file_name}")

        else:
            raise ValueError("Web browser dependency is missing")

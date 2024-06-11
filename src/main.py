import os
import asyncio
import logging
import nltk
from bootstrap import logger, Config
from classes import ToolsLoader, ChatAPIService, ResponseHandler

nltk.download("punkt")


class ChatbotApp:
    def __init__(self):
        self.api_key: str = Config.OPENAI_API_KEY
        self.system_message: str = Config.SYSTEM_MESSAGE
        self.chat_api_service: ChatAPIService
        self.response_handler: ResponseHandler
        self.tools_loader: ToolsLoader = self.setup_tools_loader()
        self.chat_api_service, self.response_handler = self.setup_chat_services()

    def get_absolute_path(self, relative_path) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "..", "config", "tools.yaml")

    def setup_tools_loader(self) -> str:
        tools_definition_file = self.get_absolute_path("../config/tools.yaml")
        tools_loader = ToolsLoader(tools_definition_file)
        tools_loader.load_tools()
        return tools_loader

    def setup_chat_services(
        self, model_name="gpt-4o", temperature=1.0
    ) -> tuple[ChatAPIService, ResponseHandler]:
        chat_api_service = ChatAPIService(self.api_key, model_name, temperature)
        response_handler = ResponseHandler()
        return chat_api_service, response_handler

    def initialize_new_message(self) -> list[dict[str, str]]:
        return [{"role": "system", "content": self.system_message}]

    def is_quit_command(self, user_input) -> bool:
        return user_input.lower() in ["quit", "exit"]

    def add_user_message(self, messages, user_input) -> None:
        messages.append({"role": "user", "content": user_input})

    def add_assistant_message(self, messages, assistant_response) -> None:
        messages.append({"role": "assistant", "content": assistant_response})

    def extract_assistant_response(self, response) -> str:
        return response["choices"][0]["message"]["content"]

    async def run(self) -> None:
        while True:
            messages = self.initialize_new_message()
            user_input = input("User: ")
            if self.is_quit_command(user_input):
                print("Goodbye!")
                break
            self.add_user_message(messages, user_input)
            response = self.chat_api_service.execute_api_call(
                messages, self.tools_loader.tools
            )
            self.response_handler.handle_response(response)
            assistant_response = self.extract_assistant_response(response)
            logger.info(assistant_response)
            # self.add_assistant_message(messages, assistant_response)


async def main() -> None:
    app = ChatbotApp()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

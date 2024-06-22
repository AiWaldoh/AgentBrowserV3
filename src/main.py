import os
import asyncio
import nltk
from bootstrap import logger, Config
from classes import ToolsLoader, BaseResponseHandler
from web_browser import WebBrowser
from http_api import ChatAPIService
from tasks import DependenciesContainer
import json
import time
from colorama import init, Fore, Style
from agentThree import FormParsingAgent

# nltk.download("punkt")


def print_welcome_message():
    init()  # Initialize colorama for color support

    # Clear the console screen
    os.system("cls" if os.name == "nt" else "clear")

    # Define the ASCII art
    ascii_art = r"""
    {cyan}╔════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                ║
    ║        {green}██╗    ██╗███████╗██╗      ██████╗ ██████╗ ███╗   ███╗███████╗{cyan}          ║
    ║        {green}██║    ██║██╔════╝██║     ██╔════╝██╔═══██╗████╗ ████║██╔════╝{cyan}          ║
    ║        {green}██║ █╗ ██║█████╗  ██║     ██║     ██║   ██║██╔████╔██║█████╗{cyan}            ║
    ║        {green}██║███╗██║██╔══╝  ██║     ██║     ██║   ██║██║╚██╔╝██║██╔══╝{cyan}            ║
    ║        {green}╚███╔███╔╝███████╗███████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║███████╗{cyan}          ║
    ║         {green}╚══╝╚══╝ ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝{cyan}          ║
    ║                                                                                ║
    ║                  {yellow}★ Your Ultimate CLI Browser Experience ★{cyan}                      ║
    ║                                                                                ║
    ║  {magenta}Get ready to embark on a captivating journey through the realms of the web!{cyan}   ║
    ║    {magenta}Prepare to witness the fusion of power, convenience, and innovation.{cyan}        ║
    ║        {magenta}Brace yourself for an unparalleled browsing adventure like{cyan}              ║
    ║                        {magenta}no other, right in your CLI!{cyan}                            ║
    ║                                                                                ║
    ╚════════════════════════════════════════════════════════════════════════════════╝
    """

    # Print the ASCII art with colors
    print(
        ascii_art.format(
            cyan=Fore.CYAN, green=Fore.GREEN, yellow=Fore.YELLOW, magenta=Fore.MAGENTA
        )
    )

    # Print additional information with typewriter effect
    typewriter_text = f"\n{Fore.CYAN}   Prepare to unleash the full potential of the web at your fingertips!{Style.RESET_ALL}"
    for char in typewriter_text:
        print(char, end="", flush=True)
        time.sleep(0.05)

    # Wait for a short pause before clearing the screen
    time.sleep(2)
    print("\n")


print_welcome_message()


class ChatbotApp:
    def __init__(self):
        self.api_key: str = Config.OPENAI_API_KEY
        self.system_message: str = Config.SYSTEM_MESSAGE
        self.web_browser: WebBrowser = WebBrowser()
        self.tools_loader: ToolsLoader = self.setup_tools_loader()
        self.chat_api_service, self.response_handler = self.setup_chat_services()

    def get_absolute_path(self, relative_path) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "..", "config", "tools.yaml")

    def setup_tools_loader(self) -> ToolsLoader:
        tools_definition_file = self.get_absolute_path("../config/tools.yaml")
        tools_loader = ToolsLoader(tools_definition_file)
        tools_loader.load_tools()
        return tools_loader

    def setup_chat_services(
        self, model_name="gpt-4o", temperature=1.0
    ) -> tuple[ChatAPIService, BaseResponseHandler]:
        chat_api_service = ChatAPIService(self.api_key, model_name, temperature)
        # Dependency Injection for response handler with default TaskExecutorStrategy
        dependencies_container = DependenciesContainer(
            web_browser=self.web_browser, tools_loader=self.tools_loader
        )
        response_handler = BaseResponseHandler(dependencies_container)
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

    def get_user_question(self):
        messages = self.initialize_new_message()

        user_input = input("User: ")

        self.add_user_message(messages, user_input)
        return messages

    async def process_results_with_agent(self, prompt, response):
        print("Processing results with AI agent...")

        agent = FormParsingAgent(self.chat_api_service)
        agent_response = await agent.determine_relevant_form_selectors(response, prompt)
        # logger.info(agent_response)
        # print(agent_response)
        # with open("res.json", "w") as file:
        #     json.dump(results, file, indent=4)
        # Placeholder method for processing results with AI agent
        # This should be replaced with the actual implementationresponse
        return "OK"

    async def run(self) -> None:
        running = True
        # Launch web browser
        await self.web_browser.launch()
        # Create dependencies injector container for browser and pass it to handle_response
        # dependencies_container = DependenciesContainer(web_browser=self.web_browser)

        while running:
            user_message = self.get_user_question()

            api_response = self.chat_api_service.execute_api_call(
                user_message, tools=self.tools_loader.tools
            )

            await self.response_handler.handle_response(api_response)
            # if result:
            #     # Process results further or send to AI agent
            #     # you need to put the agent elsewhere, since it needs to ask a follow up question
            #     # I usually test with goto, and the agent I say I want to buy a plane ticket. So do something to transition in between
            #     # if its not a function call, maybe its an agent question?
            #     print("Sending results to AI agent...")
            #     agent_response = await self.process_results_with_agent(
            #         user_message, result
            #     )
            # Handle chat history
            assistant_response = self.extract_assistant_response(api_response)
            logger.info(assistant_response)


async def main() -> None:
    app = ChatbotApp()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

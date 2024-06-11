import os
import asyncio
import logging
import nltk
from bootstrap import logger, Config
from classes import ToolsLoader, ChatAPIService, ResponseHandler

nltk.download("punkt")


def get_absolute_path(relative_path):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "..", "config", "tools.yaml")


TOOLS_DEFINITION_FILE = get_absolute_path("../config/tools.yaml")


async def main():
    api_key = Config.OPENAI_API_KEY
    system_message = Config.SYSTEM_MESSAGE

    tools_loader: ToolsLoader = setup_tools_loader()
    chat_api_service, response_handler = setup_chat_services(api_key)

    while True:
        messages = initialize_new_message(system_message)

        user_input = get_user_input_from_cli()
        if is_quit_command(user_input):
            print("Goodbye!")
            break

        add_user_message(messages, user_input)
        response = chat_api_service.execute_api_call(messages, tools_loader.tools)
        response_handler.handle_response(response)

        assistant_response = extract_assistant_response(response)
        print(assistant_response)
        # add_assistant_message(messages, assistant_response)


def get_user_input_from_cli():
    user_input = input("User: ")
    return user_input


def setup_tools_loader():
    tools_loader = ToolsLoader(TOOLS_DEFINITION_FILE)
    tools_loader.load_tools()
    return tools_loader


def setup_chat_services(api_key, model_name="gpt-4o", temperature=1.0):
    chat_api_service = ChatAPIService(api_key, model_name, temperature)
    response_handler = ResponseHandler()
    return chat_api_service, response_handler


def initialize_new_message(system_prompt):
    return [{"role": "system", "content": system_prompt}]


def is_quit_command(user_input):
    return user_input.lower() in ["quit", "exit"]


def add_user_message(messages, user_input):
    messages.append({"role": "user", "content": user_input})


def add_assistant_message(messages, assistant_response):
    messages.append({"role": "assistant", "content": assistant_response})


def extract_assistant_response(response):
    return response["choices"][0]["message"]["content"]


if __name__ == "__main__":
    asyncio.run(main())

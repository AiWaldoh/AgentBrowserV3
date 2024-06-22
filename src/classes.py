import yaml
from tasks import TaskExecutor, AITaskRegistry, GoToPageTask, InteractWithFormTask


class MessageHandler:
    def __init__(self, successor=None):
        self._successor = successor

    async def handle(self, message, dependencies_container):
        if self._can_handle(message):
            return await self._handle(message, dependencies_container)
        elif self._successor:
            return await self._successor.handle(message, dependencies_container)

    def _can_handle(self, message):
        raise NotImplementedError

    async def _handle(self, message, dependencies_container):
        raise NotImplementedError


class ToolCallMessageHandler(MessageHandler):
    def _can_handle(self, message):
        return "tool_calls" in message

    async def _handle(self, message, dependencies_container):
        results = []
        for tool_call in message["tool_calls"]:
            task_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            result = await TaskExecutor.execute_task(
                task_name, arguments, dependencies_container
            )
            results.append(result)  # Collect results
        return results


class ContentMessageHandler(MessageHandler):
    def __init__(self, conversation_history, successor=None):
        super().__init__(successor)
        self._conversation_history = conversation_history

    def _can_handle(self, message):
        return "content" in message

    async def _handle(self, message, dependencies_container):
        self._conversation_history.append(
            {"role": "assistant", "content": message["content"]}
        )


class TaskExecutorStrategy:
    async def execute(self, task_name, arguments, dependencies_container):
        raise NotImplementedError


class DefaultTaskExecutor(TaskExecutorStrategy):
    async def execute(self, task_name, arguments, dependencies_container):
        # Default task execution logic
        return await TaskExecutor.execute_task(
            task_name, arguments, dependencies_container
        )


class BaseResponseHandler:
    def __init__(self, dependencies_container, executor_strategy=None):
        self._conversation_history = []
        self._dependencies_container = dependencies_container
        self._executor_strategy = (
            executor_strategy if executor_strategy else DefaultTaskExecutor()
        )
        self._build_chain()

    def _build_chain(self):
        self.chain = ToolCallMessageHandler(
            successor=ContentMessageHandler(
                conversation_history=self._conversation_history
            )
        )

    async def handle_response(self, response):
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            if "message" in choice:
                results = await self.chain.handle(
                    choice["message"], self._dependencies_container
                )
                return results
            else:
                print(f"No message found in the response.")
        else:
            print(f"API response: {response}")

    def add_user_message(self, message):
        self._conversation_history.append({"role": "user", "content": message})

    def get_conversation_history(self):
        return self._conversation_history


class ToolsLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tools = []

    def load_tools_from_yaml(self):
        with open(self.file_path, "r") as file:
            tools_data = yaml.safe_load(file)
            self.tools = tools_data["tools"]

    def load_tools(self):
        self.load_tools_from_yaml()
        self.register_tools()

    def register_tools(self):
        for tool_data in self.tools:
            tool_name = tool_data["function"]["name"]
            tool_class = self.get_tool_class(tool_name)
            AITaskRegistry.register(tool_name, tool_class())

    def get_tool_class(self, tool_name):
        tool_class_name = (
            "".join(word.capitalize() for word in tool_name.split("_")) + "Task"
        )
        return globals()[tool_class_name]

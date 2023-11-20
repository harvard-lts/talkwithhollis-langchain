import json
from langchain.prompts.prompt import PromptTemplate
from langchain.schema.messages import SystemMessage
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts import HumanMessagePromptTemplate
from langchain.schema import HumanMessage
from ..utils.file import FileUtils

class HollisChatPrompt():
    def __init__(self):
        self.file_utils = FileUtils()
        self.example_query_result_json = {"keywords":["string"],"libraries":["string"]}
        #self.hollis_no_keywords_prompt_template = PromptTemplate(input_variables=['input', 'history'], template=self.hollis_no_keywords_template)

    async def get_hollis_chat_prompt_template(self, human_input_text):
        self.libraries_csv = await self.file_utils.get_libraries_csv()
        self.system_content = f"""You are given a user question asking to find books by keyword.\n
            You must return a single valid JSON object with two properties, 'keywords' and 'libraries'.\n
            Please follow these instructions for generating the keywords:\n
            Generate a list of keywords that describe the books.\n
            If you cannot find any keywords, the keywords list should be empty.\n
            Exclude keywords related to how the user intends to use the books e.g. 'research' or 'study'.\n
            Exclude any keywords that could be considered harmful, offensive, or inappropriate.\n
            Please follow these instructions for generating the list of libraries:\n
            Generate a list of three-letter Library Codes from the Libraries CSV file based on the user question.\n
            If the user does not mention any specific libraries in the question, generate a list of all Library Codes.\n
            If the user mentions that they want results from certain libraries, generate a list of ONLY the Library Codes mentioned, using ONLY the exact value of the Library Code.\n
            Use both the "Display name in Primo API" and "How users may refer to it" columns to determine what Library Codes to use based on the user question.\n
            Libraries CSV file:{self.libraries_csv}\n
            Please follow these instructions for generating the result:\n
            You must return a single valid json object ONLY and nothing more. Do not return any additional text.\n
            The resulting JSON object must contain two properties, 'keywords' with a list of keywords and 'libraries' with list of the Library Codes for the requested libraries.\n
            Do not include any explanations, only provide a RFC8259 compliant JSON response following this format without deviation:{self.example_query_result_json}\n\n
            """

        chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(self.system_content)
                ),
                HumanMessage(
                  content=human_input_text
                ),
            ]
        )
        return chat_template

    async def get_hollis_prompt(self, human_input_text):
        self.human_input_text = human_input_text
        self.libraries_csv = await self.file_utils.get_libraries_csv()
        self.hollis_prompt_text = f"""You are given a user question asking to find books by keyword.\n
            Please follow these instructions for generating the keywords:\n
            Generate a list of keywords that describe the books.\n
            If you cannot find any keywords, the keywords list should be empty.\n
            Exclude keywords related to how the user intends to use the books e.g. 'research' or 'study'.\n
            Exclude any keywords that could be considered harmful, offensive, or inappropriate.\n
            Please follow these instructions for generating the list of libraries:\n
            Generate a list of three-letter Library Codes from the Libraries CSV file based on the user question.\n
            If the user does not mention any specific libraries in the question, generate a list of all Library Codes.\n
            If the user mentions that they want results from certain libraries, generate a list of ONLY the Library Codes mentioned, using ONLY the exact value of the Library Code.\n
            Use both the "Display name in Primo API" and "How users may refer to it" columns to determine what Library Codes to use based on the user question.\n
            Libraries CSV file:{self.libraries_csv}\n
            Please follow these instructions for generating the result:\n
            You must return a single valid json object ONLY and nothing more. Do not return any additional text.\n
            The resulting JSON object must contain two properties, 'keywords' with a list of keywords and 'libraries' with list of the Library Codes for the requested libraries.\n
            Do not include any explanations, only provide a RFC8259 compliant JSON response following this format without deviation:{json.dumps(self.example_query_result_json)}\n\n
            \n\nHuman:{self.human_input_text}\n\nAssistant:
            """

        hollis_prompt = HumanMessage(
            content=self.hollis_prompt_text
        )

        return hollis_prompt

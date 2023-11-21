import json
from langchain.prompts.prompt import PromptTemplate
from ..utils.file import FileUtils

class HollisPrompt():
    def __init__(self):
        self.file_utils = FileUtils()
        # https://github.com/langchain-ai/langchain/blob/3d74d5e24dd62bb3878fe34de5f9eefa6d1d26c7/libs/langchain/langchain/chains/api/prompt.py#L4
        self.hollis_template = """\n\nHuman:
            You are given the following user question:\n
            <user_question>\n{human_input_text}\n</user_question>\n
            Create a JSON object with properties, 'keywords' with a list of keywords and 'libraries' with list of the Library Codes for the requested libraries.\n
            Please follow these instructions to create the keywords list:\n
            <keywords_instructions>\nThe keywords property must contain a list of keywords relevant to the question.\n
            If you cannot find any keywords in the user question, do not make them up, the keywords list should be empty.\n
            </keywords_instructions>\n
            Please follow these instructions to create the libraries list:\n
            <libraries_instructions>\n
            The 'libraries' property must contain a list of ALL the three-letter Library Codes from the 'libraryCode' property in the Libraries JSON file.\n\n
            If and ONLY IF the user mentions certain libraries in the question, the list must have ONLY the Library Codes mentioned.\n
            Use both the 'primoDisplayName' and 'howUsersMayRefer' properties in the Libraries JSON file to find the corresponding library codes based on the user question.\n
            If the user does not mention any libraries, you MUST include ALL the Library Codes.\n
            Libraries JSON file:\n<libraries_json>\n{libraries_json}\n</libraries_json>\n
            </libraries_instructions>\n
            Please follow these instructions to create the JSON object result:\n
            <result_instructions>\n
            You must return a single valid json object ONLY and nothing more. Do not return any additional text.\n
            Do not include any explanations, only provide a RFC8259 compliant JSON response following this format without deviation:\n<result_format>\n{example_query_result_json}\n</result_format>
            </result_instructions>\n
            \n\nAssistant:
            """

        self.libraries = """
            The 'libraries' property must contain a list of three-letter Library Codes from the Libraries JSON file based on the user question.\n
            Start by adding ALL the library codes in the Libraries JSON file, using ONLY the exact value of the Library Code.\n
            If the user mentions certain libraries, the list must have ONLY the Library Codes mentioned.\n
            Use both the 'primoDisplayName' and 'howUsersMayRefer' properties in the Libraries JSON file to find the corresponding library codes based on the user question.\n
            """

        self.hollis_no_keywords_template = """You are a friendly assistant whose purpose is to carry on a conversation with a user, in order to help them find books at libraries.\n
            You MUST answer the user's message to the best of your ability.\n
        
            If the user did not ask about books, append onto your response a suggestion that would help you to understand what kinds of books they are looking for.\n\n
            Examples Suggestions:\n
            I'm looking for books to help with my research on bio engineering. I want books that are available onsite at Baker, Fung, and Widener.\n
            I'm looking for books about birds. I want books that are available onsite at Fung and Widener.\n
            I'm looking for books on dogs.\n
            I'm looking for books on dogs, especially greyhounds. They can be at any library\n

            Current conversation:
            {history}
            \n\nHuman:{input}\n\nAssistant:
            """

        #self.example_query_result_json = {
            #"keywords": ["cybercrime", "malware", "DDoS"],
            #"libraries": ["BAK", "SEC", "WID"]
        #}

        self.example_query_result_json = {"keywords":["string"],"libraries":["string"]}

        self.hollis_prompt_template = PromptTemplate.from_template(template=self.hollis_template)
        self.hollis_no_keywords_prompt_template = PromptTemplate(input_variables=['input', 'history'], template=self.hollis_no_keywords_template)

    async def get_hollis_prompt_formatted(self, human_input_text):
        self.libraries_json = await self.file_utils.get_libraries_csv()
        # format the prompt to add variable values
        hollis_prompt_formatted: str = self.hollis_prompt_template.format(
            human_input_text=human_input_text,
            libraries_json=json.dumps(self.libraries_json),
            example_query_result_json=json.dumps(self.example_query_result_json),
        )
        return hollis_prompt_formatted

    async def get_hollis_no_keywords_prompt(self):
      return self.hollis_no_keywords_prompt_template

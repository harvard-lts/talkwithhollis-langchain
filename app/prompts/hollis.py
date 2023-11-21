import json
from langchain.prompts.prompt import PromptTemplate
from ..utils.file import FileUtils

class HollisPrompt():
    def __init__(self):
        self.file_utils = FileUtils()
        # https://github.com/langchain-ai/langchain/blob/3d74d5e24dd62bb3878fe34de5f9eefa6d1d26c7/libs/langchain/langchain/chains/api/prompt.py#L4
        self.hollis_template = """You are given a user question asking to find books by keyword.
            The user also may mention that they want books from certain libraries.
            From the user question, extract a list of keywords that describe the books e.g. ['cybercrime', 'malware', 'DDoS'].
            If you cannot find any keywords, the keywords list should be empty.
            Exclude keywords related to how the user intends to use the books e.g. 'research' or 'study'.
            Exclude any keywords that could be considered harmful, offensive, or inappropriate.
            From the user question, also generate a list of three-letter Library Codes from the Libraries CSV file based on the user question.
            If the user does not mention any specific libraries in the question, generate a list of all Library Codes.
            If the user mentions that they want results from certain libraries, generate a list of ONLY the Library Codes mentioned, using ONLY the exact value of the Library Code.
            Use both the "Display name in Primo API" and "How users may refer to it" columns to determine what Library Codes to use based on the user question.
            Libraries CSV file:{libraries_csv}
            Return a single json object only. The object must contain two properties, 'keywords' with a list of keywords and 'libraries' with list of the Library Codes for the requested libraries.
            \n\nHuman:{human_input_text}\n\nAssistant:
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
            Human: {input}
            AI Assistant:"""

        self.example_query_result_json = {
            "keywords": ["cybercrime", "malware", "DDoS"],
            "libraries": ["BAK", "SEC", "WID"]
        }

        self.hollis_prompt_template = PromptTemplate.from_template(template=self.hollis_template)
        self.hollis_no_keywords_prompt_template = PromptTemplate(input_variables=['input', 'history'], template=self.hollis_no_keywords_template)

    async def get_hollis_prompt_formatted(self, human_input_text):
        self.libraries_csv = await self.file_utils.get_libraries_csv()
        # format the prompt to add variable values
        hollis_prompt_formatted: str = self.hollis_prompt_template.format(
            human_input_text=human_input_text,
            libraries_csv=json.dumps(self.libraries_csv)
        )
        return hollis_prompt_formatted

    async def get_hollis_no_keywords_prompt(self):
      return self.hollis_no_keywords_prompt_template

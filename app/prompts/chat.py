import json
from langchain.prompts.prompt import PromptTemplate
from langchain.schema.messages import SystemMessage
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts import HumanMessagePromptTemplate
from ..utils.file import FileUtils

class ChatPrompt():
    def __init__(self):
        self.file_utils = FileUtils()
        self.libraries_json = self.file_utils.convert_libraries_csv_to_json()
        self.example_chat_result_json = {
            "LAM": [
                {
                    "title": ["The Art of Computer Programming"],
                    "author": ["Knuth, Peter"],
                    "callNumber": "(QA76.6 .K64 1997)"
                }
            ],
            "FUN": [
                {
                    "title": ["The Art of Computer Programming"],
                    "author": ["Knuth, Peter"],
                    "callNumber": "(QA76.6 .K64 1997)"
                },
                {
                    "title": ["A Book About Dogs"],
                    "author": ["Smith, John"],
                    "callNumber": "(PZ76.6 .K64 1996)"
                }
            ]
        }

        self.system_content = f"""You are a friendly assistant who helps to find information about the locations and availability of books in a network of libraries.\n
              Library Codes are three-letter codes that can be used to reference library names in the Libraries_JSON.\n
              You will receive a list of Library Codes. You will also receive a JSON list of books, containing titles, authors, and locations. Each location will contain a library code and call number.\n
              You will need to display the library hours for each, and then display the books in the list, grouped by library code.\n
              If a book's call number is inside parenthesis, do not include the parenthesis in the display.\n
              Below is the list format:\n\n

              Library Display name in Primo API
              Library Hours
              1.  Full book title / Author's Last Name
                  Call number
              2.  Full book title  / Author's Last Name
                  Call number
              
              \n\n
              Below is an example input and output with example data:\n
              input json:\n
              {json.dumps(self.example_chat_result_json)}
              
              output:
              Here are some books I found for you:\n

              Fung Library
              9:00am - 5:00pm
              1.  The Art of Computer Programming / Knuth
                  QA76.6 .K64 1997
              2.  A Book About Dogs / Smith
                  PZ76.6 .K64 1996

              Lamont Library
              9:00am-5:00
              1.  The Art of Computer Programming / Knuth
                  QA76.6 .K64 1997
              
              Libraries_JSON:{json.dumps(self.libraries_json)}
              """

    async def get_chat_prompt_template(self):
        human_template = "{human_input_text}"
        chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(self.system_content)
                ),
                HumanMessagePromptTemplate.from_template(human_template),
            ]
        )
        return chat_template
      
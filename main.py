#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import os, requests, json
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import APIChain
from langchain.schema import HumanMessage
from langchain.schema.messages import SystemMessage
from langchain.schema import BaseOutputParser
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts import HumanMessagePromptTemplate

from langchain.agents import create_json_agent, AgentExecutor
from langchain.agents.agent_toolkits import JsonToolkit
from langchain.chains import LLMChain
from langchain.requests import TextRequestsWrapper
from langchain.tools.json.tool import JsonSpec

llm = OpenAI(temperature=0)
chat_model = ChatOpenAI()

openai_api_key = os.environ.get("OPENAI_API_KEY")
primo_api_key = os.environ.get("PRIMO_API_KEY")
primo_api_host = os.environ.get("PRIMO_API_HOST")

system_content = """You are a friendly assistant who helps to find information about books.
A user will pass in a book subject, and you should generate a comma separated, unnumbered list of books related to that subject.
ONLY return a json list of book titles, their authors, and their descriptions, and nothing more."""
human_template = "I'm looking for books on this subject: {subject}"

# https://developers.exlibrisgroup.com/primo/apis/search/
# https://developers.exlibrisgroup.com/wp-content/uploads/primo/openapi/primoSearch.json
primo_api_docs = f"""
  Instructions for generating parameters dynamically are indicated in parantheses.\n\n
  HTML documentation: https://developers.exlibrisgroup.com/primo/apis/docs/primoSearch/R0VUIC9wcmltby92MS9zZWFyY2g=/#queryParameters
  JSON schema: https://developers.exlibrisgroup.com/wp-content/uploads/primo/openapi/primoSearch.json
  BASE URL: {primo_api_host}\n\n
  Request: GET /primo/v1/search\n\n
  Search query parameters:\n\n
  (q should be generated based on human input question e.g. any,contains,dogs as companions)\n\n
  q=<field_1>,<precision_1>,<value_1>[[,<operator_1>];<field_n>,<precision_n>,<value_n>...]
    * field - The data field that you want to search within. The following fields are valid: any (for any field), title, creator (for author), sub (for subject), and usertag (for tag).
    * precision - The precision operation that you want to apply to the field. The following precision operators are valid: exact (value must match the data in the field exactly), begins_with (the value must be found at the beginning of the field), and contains (the value must be found anywhere in the field).
    * value - The search terms, which can be a word, phrase, or exact phrase (group of words enclosed by quotes), and can include the following logical operators: AND, OR, and NOT. For more information regarding search terms, see Performing Basic Searches.
    * operator - When specifying multiple search fields for advanced searches, this parameter applies the following logical operations between fields: AND (specified values must be found in both fields), OR (specified values must be found in at least one of the fields), NOT (the specified value of the next field must not be found). If no operator is specified, the system defaults to AND.

    Note: Multiple fields are delimited by a semicolon.
    Limitation: The value must not include a semicolon character.

    In the following example, the system searches for all records in which the word home is found anywhere within the record's title:
    q=title,contains,home

    In the following example, the system searches for all records in which the title field contains the words pop and music and the subject field contains the word korean:
    q=title,contains,pop music,AND;sub,contains,korean
  lang=<language> (language ISO 639-1 language code e.g. 'sp' or 'en' should be automatically deteted based on human input question)\n\n
  Hard-coded parameters (must equal these exact values):\n\n
  scope=default_scope\n\n
  tab=books\n\n
  vid=HVD2\n\n
  limit=10\n\n
  offset=0\n\n
  API Key:\n\n
  apikey={primo_api_key}\n\n
  """

chat_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content=(system_content)
        ),
        HumanMessagePromptTemplate.from_template(human_template),
    ]
)

class JSONOutputParser(BaseOutputParser):
		def parse(self, text: str):
			return json.loads(text)

#chain = chat_template | chat_model | JSONOutputParser()
#chat_result = chain.invoke({"subject": "dogs"})

#print(chat_result)
headers = {"Content-Type": "application/json"}
chain = APIChain.from_llm_and_api_docs(llm, primo_api_docs, headers=headers, verbose=True)

#api_result = chain.run("Generate a GET request to search the Primo API to find books about dogs.")
api_result = chain.invoke("Generate a GET request to search the Primo API to find books about dogs and cats.")
print(api_result)

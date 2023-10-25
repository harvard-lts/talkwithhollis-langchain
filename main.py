#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import os
import json
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import APIChain
from langchain.schema import HumanMessage
from langchain.schema.messages import SystemMessage
from langchain.schema import BaseOutputParser
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts import HumanMessagePromptTemplate

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
primo_api_docs = f"""
  BASE URL: {primo_api_host}\n\n
  Request: GET /primo/v1/search\n\n
  Search query parameters:\n\n
  q=any,contains,<search_term> (search_term should be generated based on human input question)\n\n
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
api_result = chain.run("Generate a GET request to search the Primo API to find books about dogs.")
print(api_result)

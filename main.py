#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import os
import json
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.schema.messages import SystemMessage
from langchain.schema import BaseOutputParser
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts import HumanMessagePromptTemplate
chat_model = ChatOpenAI()

openai_api_key = os.environ.get("OPENAI_API_KEY")
primo_api_key = os.environ.get("PRIMO_API_KEY")

system_content = """You are a friendly assistant who helps to find information about books.
A user will pass in a book subject, and you should generate a comma separated, unnumbered list of books related to that subject.
ONLY return a json list of book titles, their authors, and their descriptions, and nothing more."""
human_template = "I'm looking for books on this subject: {subject}"

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

chain = chat_template | chat_model | JSONOutputParser()
chat_result = chain.invoke({"subject": "dogs"})

print(chat_result)

#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import os
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
A user will pass in a book subject, and you should generate a list of books related to that subject.
ONLY return information related to the books they ask about, and nothing more."""
human_template = "I'm looking for books on this subject: {subject}"

chat_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content=(system_content)
        ),
        HumanMessagePromptTemplate.from_template(human_template),
    ]
)

chat_result = chat_model(chat_template.format_messages(subject='dogs'))
print(chat_result)

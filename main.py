#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import os
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

openai_api_key = os.environ.get("OPENAI_API_KEY")

primo_api_key = os.environ.get("PRIMO_API_KEY")

llm = OpenAI()
#chat_model = ChatOpenAI()

#llm_result = llm.predict("hieeeeeee!")
#print(llm_result)

#chat_result = chat_model.predict("hi!")
#print(chat_result)

#text = "What would be a good company name for a company that makes colorful socks?"

#llm.predict(text)

#chat_model.predict(text)

text = "What would be a good company name for a company that makes colorful socks?"
messages = [HumanMessage(content=text)]

llm.predict_messages(messages)
# >> Feetful of Fun

chat_model.predict_messages(messages)
# >> Socks O'Color
#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import asyncio, os, requests, json, csv
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import APIChain
from langchain.schema import HumanMessage
from langchain.schema.messages import SystemMessage
from langchain.schema import BaseOutputParser
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts import HumanMessagePromptTemplate
from langchain.chains.api.prompt import API_RESPONSE_PROMPT, API_URL_PROMPT

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

async def open_csv_file(path):
    rows = []
    with open(path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            # Process each row asynchronously
            processed_row = await process_row(row)
            rows.append(processed_row)
    return rows

async def open_text_file(path):
    with open(path, 'r') as f:
        return f.read()

async def open_json_file(path):
    with open(path) as json_file:
        json_data = json.load(json_file)
        return json_data

async def process_row(row):
    # Perform some processing on each row asynchronously
    return row

async def main():
    libraries_csv = await open_csv_file('schemas/libraries.csv')
    primo_api_docs = await open_text_file('schemas/primo_api_docs.txt')
    primo_api_schema = await open_json_file('schemas/primo_api_schema.json')
    primo_api_docs = primo_api_docs.replace('primo_api_host', primo_api_host)
    primo_api_docs = primo_api_docs.replace('primo_api_key', primo_api_key)
    primo_api_docs = primo_api_docs.replace('libraries_csv', '{}'.format(libraries_csv))
    print(primo_api_docs)

    # https://developers.exlibrisgroup.com/primo/apis/search/
    # https://developers.exlibrisgroup.com/wp-content/uploads/primo/openapi/primoSearch.json
    """ Step 1: Generate API request to HOLLIS based on human input question """
    headers = {"Content-Type": "application/json"}
    # https://github.com/langchain-ai/langchain/blob/3d74d5e24dd62bb3878fe34de5f9eefa6d1d26c7/libs/langchain/langchain/chains/api/prompt.py#L4
    get_request_chain = LLMChain(llm=llm, prompt=API_URL_PROMPT)

    human_input_prefix = "Generate a GET request to search the Primo API to find books to answer the human's input question: "
    human_input_text = "I'm looking for books to help with my research on bio engineering. I want books that are available onsite."
    human_input_text_it = "Sto cercando libri che mi aiutino nelle mie ricerche sulla bioingegneria. Voglio libri disponibili in sede nella biblioteca."
    human_input_question = "{} {}".format(human_input_prefix, human_input_text)

    #api_result = chain.run("Generate a GET request to search the Primo API to find books about dogs.")
    #api_result = chain.invoke("Generate a GET request to search the Primo API to find books to answer the human's input question. {human_input_question}".format(human_input_question=human_input_question))
    primo_api_request = get_request_chain.run(question=human_input_question, api_docs=primo_api_docs)
    print(primo_api_request.replace(primo_api_key, "PRIMO_API_KEY"))

    """ Step 2: Write logic to filter, reduce, and prioritize data from HOLLIS """

    """ Step 3: Context injection into the chat prompt """

    system_content = """You are a friendly assistant who helps to find information about the locations and availability of books in a network of libraries.
    ONLY return information about books related to their question, the locations where the books can be reserved, their availability, and nothing more."""
    human_template = "{human_input_text}"

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
    #chat_result = chain.invoke({"human_input_text": "I am looking for books about dogs"})

    #print(chat_result)

asyncio.run(main())

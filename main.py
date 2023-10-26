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
from langchain.chains.api.prompt import API_RESPONSE_PROMPT, API_URL_PROMPT

from langchain.agents import create_json_agent, AgentExecutor
from langchain.agents.agent_toolkits import JsonToolkit
from langchain.chains import LLMChain
from langchain.requests import TextRequestsWrapper
from langchain.tools.json.tool import JsonSpec
import asyncio
import csv

llm = OpenAI(temperature=0)
chat_model = ChatOpenAI()
openai_api_key = os.environ.get("OPENAI_API_KEY")
primo_api_key = os.environ.get("PRIMO_API_KEY")
primo_api_host = os.environ.get("PRIMO_API_HOST")

async def open_csv_file():
    rows = []
    with open('libraries.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            # Process each row asynchronously
            processed_row = await process_row(row)
            rows.append(processed_row)
    return rows

async def process_row(row):
    # Perform some processing on each row asynchronously
    return row

async def main():
    libraries_csv = await open_csv_file()
    print(libraries_csv)

    # https://developers.exlibrisgroup.com/primo/apis/search/
    # https://developers.exlibrisgroup.com/wp-content/uploads/primo/openapi/primoSearch.json
    primo_api_docs = f"""
      (Instructions for generating parameters dynamically are indicated in parantheses.)\n\n
      HTML documentation: https://developers.exlibrisgroup.com/primo/apis/docs/primoSearch/R0VUIC9wcmltby92MS9zZWFyY2g=/#queryParameters
      JSON schema: https://developers.exlibrisgroup.com/wp-content/uploads/primo/openapi/primoSearch.json
      BASE URL: {primo_api_host}\n\n
      Request: GET /primo/v1/search\n\n
      Required hard-coded parameters:\n\n
          (these required parameters must be hard-coded to these exact values)\n\n
          facet=rtype,include,books\n\n
          scope=default_scope\n\n
          tab=books\n\n
          vid=HVD2\n\n
          limit=1\n\n
          offset=0\n\n
          apikey={primo_api_key}\n\n
      Required dynamic search query parameters:\n\n
          (these required parameters are must be generated dynamically based on human input question)\n\n
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
          (language ISO 639-1 language code e.g. 'en' should be automatically deteted based on human input question)\n\n
          lang=<language>\n\n
          (facet 'tlevel' should be generated based on human input question. please always set the 'tlevel' facet. the default 'tlevel' value should be 'facet=tlevel,include,available' to return books that are available onsite OR in storage. if they want books that are available on-site only, use this facet query: 'facet=tlevel,include,available_onsite' \n\n
          facet=tlevel,include,<available or available_onsite>
          (facet 'library' should be generated using Library Codes from the "libraries_csv" csv file. the "libraries_csv" csv file is in between '>>>' and '<<<' at the bottom of this documentation. please create a new facet for each library code, e.g. 'facet=library,include,<Library Code 1>&facet=library,include,<Library Code 2>&&facet=library,include,<Library Code n>'. if the user does not mention any specific libraries, please include all library codes in the "libraries_csv" csv file. if the user mentions that they want results from certain libraries, please create an individual facet for EACH library that is mentioned in the question. please use both the "Display name in Primo API" and "How users may refer to it" in the "libraries_csv" csv file to determine what library codes to use based on the human input question. for example, if they ask "I want books in Lamont, Baker, or Kennedy" there should be three facets, one for Lamont, one for Baker, and one for Kennedy e.g. facet=library,include,LAM&facet=library,include,KSG&facet=library,include,BAK\n\n
          facet=library,include,<a Library Code from the "libraries_csv" csv file>
          >>>{libraries_csv}<<<
      """
    print(primo_api_docs)
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
    print(primo_api_request)

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

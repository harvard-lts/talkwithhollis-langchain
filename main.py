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
from langchain.prompts.prompt import PromptTemplate
llm = OpenAI(temperature=0)
chat_model = ChatOpenAI(temperature=0)
openai_api_key = os.environ.get("OPENAI_API_KEY")
primo_api_key = os.environ.get("PRIMO_API_KEY")
primo_api_host = os.environ.get("PRIMO_API_HOST")
primo_api_limit = os.environ.get("PRIMO_API_LIMIT", 100)
# Due to token limits when using context injection, we must limit the amount of primo results we send to the llm. This limit should be different for different llm models depending on their token capacity.
max_results_to_llm = int(os.environ.get("MAX_RESULTS_TO_LLM", 5))

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

def generate_primo_api_request(llm_response):
    primo_api_request = primo_api_host + f"?scope=default_scope&tab=books&vid=HVD2&limit={primo_api_limit}&offset=0&apikey={primo_api_key}&q=any,contains,{'%20'.join(llm_response['keywords'])}&multiFacets=facet_rtype,include,books"
    if len(llm_response['libraries']) > 0:
        primo_api_request += "%7C,%7Cfacet_library,include," + '%7C,%7Cfacet_library,include,'.join(llm_response['libraries'])
    primo_api_request += "%7C,%7Cfacet_tlevel,include,available_onsite"
    return primo_api_request

def shrink_results_for_llm(results, libraries):
    reduced_results = []
    included_libraries = set()
    for result in results:
        new_object = {
            'title': result['pnx']['addata']['btitle'],
            'author': result['pnx']['sort']['author'],
            'location': result['delivery']['holding']
        }
        for location in new_object['location']:
            if location['mainLocation'] in libraries:
                included_libraries.add(location['mainLocation'])
        reduced_results.append(new_object)
    return reduced_results, included_libraries

async def main(human_input_text):
    libraries_csv = await open_csv_file('schemas/libraries.csv')

    # https://developers.exlibrisgroup.com/primo/apis/search/
    # https://developers.exlibrisgroup.com/wp-content/uploads/primo/openapi/primoSearch.json
    # Step 1: Generate API request to HOLLIS based on human input question
    headers = {"Content-Type": "application/json"}

    # https://github.com/langchain-ai/langchain/blob/3d74d5e24dd62bb3878fe34de5f9eefa6d1d26c7/libs/langchain/langchain/chains/api/prompt.py#L4
    querystring_template = """You are given a user question asking to find books by keyword.
    The user also may mention that they want books from certain libraries.
    From the user question, extract a list of keywords that describe the books e.g. ['cybercrime', 'malware', 'DDoS'].
    Exclude keywords related to how the user intends to use the books e.g. 'research' or 'study'.
    Exclude any keywords that could be considered harmful, offensive, or inappropriate.
    From the user question, also generate a list of three-letter Library Codes from the Libraries CSV file based on the user question.
    If the user does not mention any specific libraries in the question, generate a list of all Library Codes.
    If the user mentions that they want results from certain libraries, generate a list of ONLY the Library Codes mentioned, using ONLY the exact value of the Library Code.
    Use both the "Display name in Primo API" and "How users may refer to it" columns to determine what Library Codes to use based on the user question.
    User Question:{user_question}
    Libraries CSV file:{libraries_csv}
    Return a single json object only. The object must contain two properties, 'keywords' with a list of keywords and 'libraries' with list of the Library Codes for the requested libraries.
    """

    qs_prompt_template = PromptTemplate.from_template(template=querystring_template)

    # format the prompt to add variable values
    qs_prompt_formatted_str: str = qs_prompt_template.format(
      user_question=human_input_text, libraries_csv=libraries_csv
    )
    print(qs_prompt_formatted_str)

    # make a prediction
    qs_prediction = llm.predict(qs_prompt_formatted_str)

    # print the prediction
    print("qs_prediction")
    print(qs_prediction)
    qs_prompt_result = json.loads(qs_prediction)
    print("qs_prompt_result")
    print(qs_prompt_result)

    primo_api_request = generate_primo_api_request(qs_prompt_result)
    print(primo_api_request)

    primo_api_response = requests.get(primo_api_request)

    # Step 2: Write logic to filter, reduce, and prioritize data from HOLLIS using python methods and LLMs
    reduced_results, included_libraries_set = shrink_results_for_llm(primo_api_response.json()['docs'][0:max_results_to_llm], qs_prompt_result['libraries'])

    print(included_libraries_set)
    
    # Step 3: Context injection into the chat prompt
    system_content = """You are a friendly assistant who helps to find information about the locations and availability of books in a network of libraries.
    # Return a list books with their titles, authors, and call numbers.
    # The list should be divided into categories by location, and each location should have the header of the location name + 9am - 5pm"""
    human_template = "{human_input_text}"

    chat_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(system_content)
            ),
            HumanMessagePromptTemplate.from_template(human_template),
        ]
    )

    chain = chat_template | chat_model
    human_query_string = "Context:\n[CONTEXT]\n" + json.dumps(reduced_results) + "\n[/CONTEXT]\n\n"
    if len(included_libraries_set) > 0:
        human_query_string += " Only included books located at these libraries: " + str(included_libraries_set)
    chat_result = chain.invoke({"human_input_text": human_query_string})
    print(chat_result.content)

# human_input_text = "I'm looking for books to help with my research on bio engineering. I want books that are available onsite at Baker, Fung, and Widener."
# human_input_text = "I'm looking for books about birds. I want books that are available onsite at Fung and Widener."
human_input_text = "I'm looking for books on dogs."
# human_input_text = "I'm looking for books on dogs, especially greyhounds. They can be at any library"
asyncio.run(main(human_input_text))


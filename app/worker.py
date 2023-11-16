#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import asyncio, os, requests, json, csv
import pandas as pd
from langchain.llms import OpenAI, AzureOpenAI
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.schema.messages import SystemMessage
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts import HumanMessagePromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts.prompt import PromptTemplate

openai_api_key = os.environ.get("OPENAI_API_KEY")
primo_api_key = os.environ.get("PRIMO_API_KEY")
primo_api_host = os.environ.get("PRIMO_API_HOST")
primo_api_limit = os.environ.get("PRIMO_API_LIMIT", 100)
# Due to token limits when using context injection, we must limit the amount of primo results we send to the llm. This limit should be different for different llm models depending on their token capacity.
max_results_to_llm = int(os.environ.get("MAX_RESULTS_TO_LLM", 5))

ai_platform = os.environ.get("AI_PLATFORM", "azure")

example_query_result_json = {
    "keywords": ["cybercrime", "malware", "DDoS"],
    "libraries": ["BAK", "SEC", "WID"]
}

example_chat_result_json = {
    "LAM": [
        {
            'title': ['The Art of Computer Programming'],
		    'author': ['Knuth, Peter'],
            "callNumber": "(QA76.6 .K64 1997)"
        }
    ],
    "FUN": [
        {
            'title': ['The Art of Computer Programming'],
		    'author': ['Knuth, Peter'],
            "callNumber": "(QA76.6 .K64 1997)"
        },
        {
            'title': ["A Book About Dogs"],
            'author': ["Smith, John"],
            "callNumber": "(PZ76.6 .K64 1996)"
        }
    ]
}

class LLMWorker():
    def __init__(self):
        self.llm = OpenAI(temperature=0)
        self.chat_model = ChatOpenAI(temperature=0)
        if (ai_platform == "azure"):
            os.environ["OPENAI_API_TYPE"] = os.environ.get("AZURE_OPENAI_API_TYPE", "azure")
            os.environ["OPENAI_API_VERSION"] = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-08-01-preview")
            os.environ["OPENAI_API_BASE"] = os.environ.get("AZURE_OPENAI_API_BASE")
            os.environ["OPENAI_API_KEY"] = os.environ.get("AZURE_OPENAI_API_KEY")
            """
            self.chat_model = AzureChatOpenAI(
                temperature=0,
                deployment_name=os.environ.get("AZURE_OPENAI_API_DEPLOYMENT", "gpt-35-turbo"),
                model_version=os.environ.get("AZURE_OPENAI_API_MODEL_VERSION", "0301"),
            )

            self.llm = AzureOpenAI(
                deployment_name=os.environ.get("AZURE_OPENAI_API_DEPLOYMENT", "gpt-35-turbo"),
                model_name=os.environ.get("AZURE_OPENAI_API_MODEL_NAME", "gpt-35-turbo"),
            )
            """

    async def open_csv_file(self, path):
        rows = []
        with open(path, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                # Process each row asynchronously
                processed_row = await self.process_row(row)
                rows.append(processed_row)
        return rows

    async def open_text_file(self, path):
        with open(path, 'r') as f:
            return f.read()

    async def open_json_file(self, path):
        with open(path) as json_file:
            json_data = json.load(json_file)
            return json_data

    async def process_row(self, row):
        # Perform some processing on each row asynchronously
        return row

    def generate_primo_api_request(self, llm_response):
        primo_api_request = primo_api_host + f"?scope=default_scope&tab=books&vid=HVD2&limit={primo_api_limit}&offset=0&apikey={primo_api_key}&q=any,contains,{'%20'.join(llm_response['keywords'])}&multiFacets=facet_rtype,include,books"
        if len(llm_response['libraries']) > 0:
            primo_api_request += "%7C,%7Cfacet_library,include," + '%7C,%7Cfacet_library,include,'.join(llm_response['libraries'])
        primo_api_request += "%7C,%7Cfacet_tlevel,include,available_onsite"
        return primo_api_request

    def shrink_results_for_llm(self, results, libraries):
        reduced_results = {}
        for result in results:
            for holding in result['delivery']['holding']:
                new_object = {
                    # TODO: We previously were using ['pnx']['addata']['btitle'] but that is not always present. We will need to come up with a prioritization order to determine which title to use.
                    'title': result['pnx']['sort']['title'],
                    # TODO: Corinna wants us to use ['pnx']['addata']['aulast'] but that author is not always present and we will need to come up with a prioritization order to determine which author to use.
                    'author': result['pnx']['sort']['author'],
                    'callNumber': holding['callNumber']
                }
                if holding['libraryCode'] in libraries:
                    if not holding['libraryCode'] in reduced_results:
                        reduced_results[holding['libraryCode']] = []
                    reduced_results[holding['libraryCode']].append(new_object)

        return reduced_results

    async def predict(self, human_input_text, conversation_history = []):
        libraries_csv = await self.open_csv_file('schemas/libraries.csv')
        df = pd.read_csv('schemas/libraries.csv')
        libraries_json = df.to_json(orient='records')

        # Currently, this prevents the llm from remembering conversations. If convo_memoory was defined outside of the context of this method, it WOULD enable remembering conversations.
        # It should be here for now because we want to simulate how an api route will not actually remember the conversation.
        convo_memory = ConversationSummaryBufferMemory(llm=self.llm, max_token_limit=650, return_messages=True)
        convo_memory.load_memory_variables({})

        print("conversation history:")
        print(conversation_history)
        for history_item in conversation_history:
            convo_memory.save_context({"input": history_item.user}, {"output": history_item.assistant})

        # https://developers.exlibrisgroup.com/primo/apis/search/
        # https://developers.exlibrisgroup.com/wp-content/uploads/primo/openapi/primoSearch.json
        # Step 1: Generate API request to HOLLIS based on human input question
        headers = {"Content-Type": "application/json"}

        # https://github.com/langchain-ai/langchain/blob/3d74d5e24dd62bb3878fe34de5f9eefa6d1d26c7/libs/langchain/langchain/chains/api/prompt.py#L4
        querystring_template = """You are a helpful AI assistant expert in identifying the relevant keywords and library codes based on the user's question about books currently available in libraries.\n
        Use following context to create the keywords and library codes. Context:\n\n
        You are given a user question asking to find books by keyword.\n
        The user also may mention that they want books from certain libraries.\n
        From the user question, extract a list of keywords that describe the books e.g. ['cybercrime', 'malware', 'DDoS'].\n
        If you cannot find any keywords, the keywords list should be empty.\n
        Exclude keywords related to how the user intends to use the books e.g. 'research' or 'study'.\n
        Exclude any keywords that could be considered harmful, offensive, or inappropriate.\n
        From the user question, also generate a list of three-letter Library Codes from the Libraries CSV file based on the user question.\n
        If the user does not mention any specific libraries in the question, generate a list of all Library Codes.\n
        If the user mentions that they want results from certain libraries, generate a list of ONLY the Library Codes mentioned, using ONLY the exact value of the Library Code.\n
        Use both the "Display name in Primo API" and "How users may refer to it" columns to determine what Library Codes to use based on the user question.\n
        User Question:\n{human_input_text}\n
        Libraries CSV file:\n{libraries_csv}\n
        Use the following format for the return value:\n\n
        Return a valid json object only.\n
        The json object must have two properties, 'keywords' and 'libraries' only.\n
        The 'keywords' value must be a list of keywords and the 'libraries' value must be a list of the Library Codes for the requested libraries.
        Example JSON result:\n{example_query_result_json}\n
        """

        qs_prompt_template = PromptTemplate.from_template(template=querystring_template)

        # format the prompt to add variable values
        qs_prompt_formatted_str: str = qs_prompt_template.format(
          human_input_text=human_input_text,
          libraries_csv=libraries_csv,
          example_query_result_json=json.dumps(example_query_result_json)
        )

        # make a prediction
        qs_prediction = self.llm.predict(qs_prompt_formatted_str)

        # print the prediction
        print("qs_prediction")
        print(qs_prediction)
        qs_prompt_result = json.loads(qs_prediction)
        print("qs_prompt_result")
        print(qs_prompt_result)

        if len(qs_prompt_result['keywords']) == 0:
            no_keywords_template = """You are a friendly assistant whose purpose is to carry on a conversation with a user, in order to help them find books at libraries.\n
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
            prompt = PromptTemplate(input_variables=['history', 'input'], template = no_keywords_template)

            conversation_with_summary = ConversationChain(
                prompt=prompt,
                llm=self.llm,
                memory=convo_memory,
                verbose=True,
            )

            no_keyword_result = conversation_with_summary.predict(input=human_input_text)
            print(no_keyword_result)
            return no_keyword_result
        else:
            primo_api_request = self.generate_primo_api_request(qs_prompt_result)
            print(primo_api_request)

            primo_api_response = requests.get(primo_api_request)

            # Step 2: Write logic to filter, reduce, and prioritize data from HOLLIS using python methods and LLMs
            reduced_results = self.shrink_results_for_llm(primo_api_response.json()['docs'][0:max_results_to_llm], qs_prompt_result['libraries'])
            print(reduced_results)
            print(reduced_results.keys())
            
            # Step 3: Context injection into the chat prompt
            system_content = f"""You are a friendly assistant who helps to find information about the locations and availability of books in a network of libraries.\n
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
            {json.dumps(example_chat_result_json)}
            
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
            
            Libraries_JSON: {json.dumps(libraries_json)}\n\n
            """

            human_template = "{human_input_text}"

            chat_template = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(
                        content=(system_content)
                    ),
                    HumanMessagePromptTemplate.from_template(human_template),
                ]
            )

            chain = chat_template | self.chat_model
            human_query_string = "Context:\n[CONTEXT]\n" + json.dumps(reduced_results) + "\n[/CONTEXT]\n\n The hours for all libraries are 9:00am - 5:00pm."
            if len(reduced_results.keys()) > 0:
                human_query_string += " Only include books located at these libraries: " + str(reduced_results.keys())
            chat_result = chain.invoke({"human_input_text": human_query_string})
            print('chat_result.content')
            print(chat_result.content)
            return chat_result.content
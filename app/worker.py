#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import asyncio, os, requests, json, csv
from langchain.llms import OpenAI, AzureOpenAI
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.schema.messages import SystemMessage
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts import HumanMessagePromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts.prompt import PromptTemplate

openai_api_key = os.environ.get("OPENAI_API_KEY")
# Due to token limits when using context injection, we must limit the amount of primo results we send to the llm. This limit should be different for different llm models depending on their token capacity.
max_results_to_llm = int(os.environ.get("MAX_RESULTS_TO_LLM", 5))

from .prompts.hollis import hollis_prompt_template
from .utils.primo import PrimoUtils
from .utils.files import FilesUtils

example_query_result_json = {
    "keywords": ["cybercrime", "malware", "DDoS"],
    "libraries": ["BAK", "SEC", "WID"]
}

example_chat_result_json = {
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

class LLMWorker():
    def __init__(self):
        self.llm = OpenAI(temperature=0)
        self.chat_model = ChatOpenAI(temperature=0)
        self.primo_utils = PrimoUtils()
        self.files_utils = FilesUtils()

    async def predict(self, human_input_text, conversation_history = []):

        libraries_json = await self.files_utils.get_libraries_json()

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

        # format the prompt to add variable values
        hollis_prompt_formatted_str: str = hollis_prompt_template.format(
            human_input_text=human_input_text,
            libraries_json=json.dumps(libraries_json),
            example_query_result_json=json.dumps(example_query_result_json)
        )

        try:
            # make a prediction
            hollis_prediction = self.llm.predict(hollis_prompt_formatted_str)
        except Exception as e:
            print('Error in hollis_prediction')
            print(e)
            return e

        # print the prediction
        print("hollis_prediction")
        print(hollis_prediction)
        try:
            # print the prediction
            hollis_prompt_result = json.loads(hollis_prediction)
        except ValueError as ve:  # includes simplejson.decoder.JSONDecodeError
            print('Unable to decode json hollis_prediction')
            print(ve)
            return ve
        print("hollis_prompt_result")
        print(hollis_prompt_result)

        if len(hollis_prompt_result['keywords']) == 0:
            no_keywords_template = """You are a friendly assistant whose purpose is to carry on a conversation with a user, in order to help them find books at libraries.\n
            You MUST answer the user's message to the best of your ability.\n
        
            If the user did not ask about books, append onto your response a suggestion that would help you to understand what kinds of books they are looking for.\n\n
            Example suggestions:\n\n
            I'm looking for books to help with my research on bio engineering. I want books that are available onsite at Baker, Fung, and Widener.\n
            I'm looking for books about birds. I want books that are available onsite at Fung and Widener.\n
            I'm looking for books on dogs.\n
            I'm looking for books on dogs, especially greyhounds. They can be at any library\n

            Current conversation: {history}\n\n
            \n\nHuman: {input}\n\nAssistant:
            """
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
            
            primo_api_request = self.primo_utils.generate_primo_api_request(hollis_prompt_result)
            print(primo_api_request)

            primo_api_response = requests.get(primo_api_request)

            # Step 2: Write logic to filter, reduce, and prioritize data from HOLLIS using python methods and LLMs
            reduced_results = self.primo_utils.shrink_results_for_llm(primo_api_response.json()['docs'][0:max_results_to_llm], hollis_prompt_result['libraries'])
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
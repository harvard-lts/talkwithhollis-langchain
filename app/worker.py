#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import asyncio, os, requests, json, csv
from langchain.llms import OpenAI, AzureOpenAI
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import HumanMessage
from openai import AzureOpenAI

openai_api_key = os.environ.get("OPENAI_API_KEY")
# Due to token limits when using context injection, we must limit the amount of primo results we send to the llm. This limit should be different for different llm models depending on their token capacity.
max_results_to_llm = int(os.environ.get("MAX_RESULTS_TO_LLM", 5))

from .prompts.hollis import HollisPrompt
from .prompts.hollischat import HollisChatPrompt
from .prompts.chat import ChatPrompt
from .utils.primo import PrimoUtils
from .utils.file import FileUtils

class LLMWorker():
    def __init__(self):
        self.llm = OpenAI(temperature=0)
        self.chat_model = ChatOpenAI(temperature=0)
        self.hollis_prompt = HollisPrompt()
        self.chat_prompt = ChatPrompt()
        self.hollis_chat_prompt = HollisChatPrompt()
        self.primo_utils = PrimoUtils()
        self.file_utils = FileUtils()
        self.ai_platform = os.environ.get("AI_PLATFORM", "azure")
        print(self.ai_platform)

        if (self.ai_platform == "azure"):
            print("setting azure config")
            #os.environ["OPENAI_API_TYPE"] = os.environ.get("AZURE_OPENAI_API_TYPE", "azure")
            #os.environ["OPENAI_API_VERSION"] = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-08-01-preview")
            #os.environ["OPENAI_API_BASE"] = os.environ.get("AZURE_OPENAI_API_BASE")
            #os.environ["OPENAI_API_KEY"] = os.environ.get("AZURE_OPENAI_API_KEY")

            print("setting azure llm start")
            self.llm = AzureOpenAI(
                #model=os.environ.get("AZURE_OPENAI_API_DEPLOYMENT", "gpt-4-1106-Preview"),
                #response_format={ "type": "json_object" },
                #model_name=os.environ.get("AZURE_OPENAI_API_MODEL_NAME", "gpt-4"),
                azure_endpoint = os.environ.get("AZURE_OPENAI_API_BASE"), 
                api_key=os.environ.get("AZURE_OPENAI_API_KEY"),  
                api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
            )
            print("setting azure llm complete")
        """
            self.chat_model = AzureChatOpenAI(
                temperature=0,
                deployment_name=os.environ.get("AZURE_OPENAI_API_DEPLOYMENT", "gpt-35-turbo"),
                model_version=os.environ.get("AZURE_OPENAI_API_MODEL_VERSION", "0301"),
            )

        """

    async def predict(self, human_input_text, conversation_history = []):

        libraries_json = self.file_utils.get_libraries_json()
        # Currently, this prevents the llm from remembering conversations. If convo_memoory was defined outside of the context of this method, it WOULD enable remembering conversations.
        # It should be here for now because we want to simulate how an api route will not actually remember the conversation.
        #convo_memory = ConversationSummaryBufferMemory(llm=self.llm, max_token_limit=650, return_messages=True)
        #convo_memory.load_memory_variables({})

        #print("conversation history:")
        #print(conversation_history)

        #for history_item in conversation_history:
            #convo_memory.save_context({"input": history_item.user}, {"output": history_item.assistant})

        # https://developers.exlibrisgroup.com/primo/apis/search/
        # https://developers.exlibrisgroup.com/wp-content/uploads/primo/openapi/primoSearch.json
        # Step 1: Generate API request to HOLLIS based on human input question
        headers = {"Content-Type": "application/json"}

        # format the prompt to add variable values
        #hollis_prompt_formatted = await self.hollis_prompt.get_hollis_prompt_formatted(human_input_text)
        hollis_prompt = await self.hollis_chat_prompt.get_hollis_prompt(human_input_text)

        hollis_prediction = None
        try:
            # get predicted keywords and libraries from the llm
            #hollis_prediction = self.llm.predict(hollis_prompt_formatted)
            #hollis_prediction = self.llm.chat.completions.create(HumanMessage(
                #content="return a json object with the top 10 largest countries by population, include the country name and approximate population size as of the latest data available",
            #))
            hollis_prediction = self.llm.chat.completions.create(
              temperature=0,
              # Model = should match the deployment name you chose for your 1106-preview model deployment
              model="gpt-4-1106-Preview",
              response_format={ "type": "json_object" },
              messages=[
                {"role": "system", "content": "The user will ask a question about a certain country. return a json object with the top 10 largest municipalities by population, include the municipality name and approximate population size as of the latest data available"},
                {"role": "user", "content": "What are the top 10 populations in Brazil?"}
              ]
            )
        except Exception as e:
            print('Error in hollis_prediction')
            print(e)
            return 'Server error'

        #hollis_prediction_json = hollis_prediction.choices[0].message.content
        # print the prediction
        
        #print("hollis_prediction_json")
        #print(hollis_prediction_json)

        """
        hollis_prompt_result = None
        try:
            # print the prediction
            hollis_prompt_result = json.loads(hollis_prediction_json)
        except ValueError as ve:  # includes simplejson.decoder.JSONDecodeError
            print('Unable to decode json hollis_prediction')
            print(ve)
            return 'Server error'
        """
        print("hollis_prediction")
        print(hollis_prediction)
        return "success"

        """
        if hollis_prompt_result is None or len(hollis_prompt_result['keywords']) == 0:
            
            hollis_no_keywords_prompt = await self.hollis_prompt.get_hollis_no_keywords_prompt()

            conversation_with_summary = ConversationChain(
                prompt=hollis_no_keywords_prompt,
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
            chat_template = await self.chat_prompt.get_chat_prompt_template()
            chain = chat_template | self.chat_model
            human_query_string = "Context:\n[CONTEXT]\n" + json.dumps(reduced_results) + "\n[/CONTEXT]\n\n The hours for all libraries are 9:00am - 5:00pm."
            if len(reduced_results.keys()) > 0:
                human_query_string += " Only include books located at these libraries: " + str(reduced_results.keys())
            chat_result = chain.invoke({"human_input_text": human_query_string})
            print('chat_result.content')
            print(chat_result.content)
            return chat_result.content
        """

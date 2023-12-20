#!/usr/bin/env python
# pipenv shell
# pipenv run python3 main.py
import asyncio, os, requests, json, csv
from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.llms.bedrock import Bedrock

from .prompts.hollis import HollisPrompt
from .prompts.chat import ChatPrompt
from .utils.primo import PrimoUtils
from .utils.file import FileUtils
from .utils.bedrock import get_bedrock_client
from .utils.libcalutils import LibCalUtils

from app.config import settings

# Due to token limits when using context injection, we must limit the amount of primo results we send to the llm. This limit should be different for different llm models depending on their token capacity.
max_results_to_llm = settings.max_results_to_llm

class LLMWorker():
    def __init__(self):
        self.hollis_prompt = HollisPrompt()
        self.chat_prompt = ChatPrompt()
        self.primo_utils = PrimoUtils()
        self.file_utils = FileUtils()

        if settings.ai_platform == "amazon" or settings.ai_platform == "aws":
            # https://github.com/aws-samples/amazon-bedrock-workshop/blob/main/01_Generation/02_contextual_generation.ipynb
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
            self.llm = Bedrock(
                # Uncomment credentials_profile_name to use a profile defined in ~/.aws/credentials
                #credentials_profile_name=os.environ.get("AWS_BEDROCK_PROFILE_NAME", "talkwithhollis"),
                region_name=settings.aws_default_region,
                model_id=settings.aws_bedrock_model_id
            )
        else:
            self.llm = OpenAI(temperature=0, openai_api_key=settings.openai_api_key)

    async def predict(self, human_input_text, conversation_history = []):

        libraries_json = self.file_utils.convert_libraries_csv_to_json()
        # Currently, this prevents the llm from remembering conversations. If convo_memoory was defined outside of the context of this method, it WOULD enable remembering conversations.
        # It should be here for now because we want to simulate how an api route will not actually remember the conversation.
        convo_memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=650,
            return_messages=True,
            human_prefix="User",
            ai_prefix="AI"
        )

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
        hollis_prompt_formatted = await self.hollis_prompt.get_hollis_prompt_formatted(human_input_text)

        hollis_prediction = None
        try:
            # make a prediction
            hollis_prediction = self.llm.predict(hollis_prompt_formatted)
        except Exception as e:
            print('Error in hollis_prediction')
            print(e)
            return 'Server error'

        # print the prediction
        print("hollis_prediction")
        print(hollis_prediction)

        hollis_prompt_result = None
        try:
            # Convert the result to json
            hollis_prompt_result = await self.file_utils.get_json_from_paragraph(hollis_prediction)
        except ValueError as ve:  # includes simplejson.decoder.JSONDecodeError
            print('Unable to decode json hollis_prediction')
            print(ve)
            return 'Server error'

        print("hollis_prompt_result")
        print(hollis_prompt_result)

        if hollis_prompt_result is None or hollis_prompt_result.get('keywords') is None or len(hollis_prompt_result.get('keywords')) == 0:
            
            hollis_no_keywords_prompt = await self.hollis_prompt.get_hollis_no_keywords_prompt()

            conversation_with_summary = ConversationChain(
                prompt=hollis_no_keywords_prompt,
                llm=self.llm,
                memory=convo_memory,
                verbose=True
            )

            no_keyword_result = conversation_with_summary.predict(input=human_input_text)
            print(no_keyword_result)
            return no_keyword_result
        else:
            self.primo_api_request = self.primo_utils.generate_primo_api_request(hollis_prompt_result)
            self.hollis_api_request = self.primo_utils.generate_hollis_api_request(hollis_prompt_result)
            print(self.primo_api_request)
            print(self.hollis_api_request)

            primo_api_response = requests.get(self.primo_api_request)

            # Step 2: Write logic to filter, reduce, and prioritize data from HOLLIS using python methods and LLMs

            # TODO: Only send books that are available to shrink_results_for_llm. Books can have more than one holding, assuming that holdings are where
            # availability is stored, this will mean 'books with at least one holding that is available'.
            reduced_results = self.primo_utils.shrink_results_for_llm(primo_api_response.json()['docs'][0:max_results_to_llm], hollis_prompt_result['libraries'])
            print(reduced_results)
            print(reduced_results.keys())
            
            # Step 3: Format the book list response. 
            return await self.build_response(reduced_results)
            
    async def build_response(self, reduced_results):
        # Config decides whether we go to the llm or just format the response through python code
        # Original functionality was using the llm, but since it's just organizing json we can accomplish the same result faster with python code
        # Functionality has been left in, but configured off, in case we find a more novel way to analyze the results using the llm in the future
        library_hours = await self.get_library_hours()
        if settings.llm_do_response_formatting == 'false':
            # Generate Python response string
            response = " Here are some books I found for you:\n\n\n"
            libraries = self.file_utils.convert_libraries_csv_to_json()
            for library_code in reduced_results:
                for library in json.loads(libraries):
                    if library["Library Code"] == library_code:
                        response += library["Display name in Primo API"] + "\n"
                        break

                if library_hours is not None and library_code in library_hours:
                        response += library_hours[library_code] + "\n"
                else:
                    response += "Operating Hours unknown, please check library website\n"

                counter = 1
                for book in reduced_results[library_code]:
                    response += str(counter) + ". " + ', '.join(book['title'])
                    if 'author' in book:
                        response += " / " + ', '.join(book['author'])
                    response += "\n"

                    if 'callNumber' in book:
                        callNumber = book['callNumber']
                        # Need to slice off the opening and closing parenthesis from call numbers, if they exist
                        if callNumber[0] == '(':
                            callNumber = callNumber[1:]

                        if callNumber[len(callNumber) - 1] == ')':
                            callNumber = callNumber[:-1]
                        response += "   " + callNumber
                    response += "\n"
                    counter += 1
                response += "\n"
            # TODO: Create a hollis link for the search results (instead of a link to the primo api)
            # TODO: Display the link as clickable in the react app (it just displays the plain text right now)
            response += "<a href='{}' target='_blank'>Click here to view the full search results in HOLLIS</a>".format(self.hollis_api_request)
            print(response)
            return response
        else:
            chat_template = await self.chat_prompt.get_chat_prompt_template()
            chain = chat_template | self.llm
            human_query_string = "Context:\n[CONTEXT]\n" + json.dumps(reduced_results) + "\n[/CONTEXT]\n\n The hours for all libraries are 9:00am - 5:00pm."
            if len(reduced_results.keys()) > 0:
                human_query_string += " Only include books located at these libraries: " + str(reduced_results.keys()) + " "
                human_query_string += "\n\nAssistant:"
            chat_result = chain.invoke({"human_input_text": human_query_string})
            print('chat_result')
            print(chat_result)
            return chat_result

    async def get_library_hours(self):
        libcal_utils = LibCalUtils()
        return await LibCalUtils.get_library_hours(libcal_utils)

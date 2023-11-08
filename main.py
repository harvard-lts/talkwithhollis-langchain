from app.worker import LLMWorker
import asyncio

# human_input_text = "I'm looking for books to help with my research on bio engineering. I want books that are available onsite at Baker, Fung, and Widener."
# human_input_text = "I'm looking for books about birds. I want books that are available onsite at Fung and Widener."
# human_input_text = "I'm looking for books on dogs."
human_input_text = "I'm looking for books on birds."
# human_input_text = "Hello, how are you?"
# human_input_text = "I'm looking for books on dogs, especially greyhounds. They can be at any library"
llm_worker = LLMWorker()
asyncio.run(llm_worker.main(human_input_text))

# while (human_input_text != "stop"):
#     human_input_text = input("")
#     asyncio.run(main(human_input_text))

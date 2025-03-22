from dotenv import load_dotenv
from pathlib import Path

# load .env file that contains the OPENAI_API_KEY
load_dotenv()

from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o", # [SC][TODO] for actual testing change the model to gpt-4o
    messages=[
        {"role": "system", "content": "You are an expert Tic-Tac-Toe player."}, # [SC][TODO] you can trying putting here the strategies (the prompt engineering you did) the model should follow
        {
            "role": "user",
            "content": "Let's play tic-tac-toe"
        },
        {
            "role": "assistant",
            "content": "Sure! Let's play Tic-Tac-Toe. The board is represented as a 3x3 grid, and you can choose X or O. \n\nHere’s the initial board:\n\n```\n1 | 2 | 3\n---------\n4 | 5 | 6\n---------\n7 | 8 | 9\n```\n\nYou can choose a position by referring to the numbers. Would you like to be X or O?"
        },
        {
            "role": "user",
            "content": "My move is 5"
        }
    ]
)
# [SC] you need to iteratively attach the model replies to the messages array to preserve the history of past conversation and provide context for your next query

# [SC] the above prints:
# ChatCompletionMessage(content="Great! You've chosen X and placed it in position 5. Here's the updated board:\n\n```\n1 | 2 | 3\n---------\n4 | X | 6\n---------\n7 | 8 | 9\n```\n\nNow it’s my turn. I’ll place O in position 1.\n\n```\n O | 2 | 3\n---------\n 4 | X | 6\n---------\n 7 | 8 | 9\n```\n\nYour turn! Where would you like to go?", refusal=None, role='assistant', audio=None, function_call=None, tool_calls=None)
print(completion.choices[0].message)

# [SC] for extracting the content or role
print(completion.choices[0].message.role)
print(completion.choices[0].message.content)

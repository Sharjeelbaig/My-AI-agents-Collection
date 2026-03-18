from src.features.agent.agent import agent
from src.features.speech_to_text.speech_to_text import get_speech_input

user_question = get_speech_input()

if user_question:
    result = agent.invoke({
        "messages": [{"role": "user", "content": user_question}]
    }, config={"configurable": {"thread_id": "thread1"}})
    print(f"\nAnswer: {result['messages'][-1].content}")
else:
    print("No valid speech input received. Please try again.")
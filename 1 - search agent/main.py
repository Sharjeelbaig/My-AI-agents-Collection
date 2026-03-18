from src.features.agent.agent import agent

result = agent.invoke({
    "messages": [{"role": "user", "content": "Who is the latest supreme leader of Iran? (one word answer only)"}]
}, config={"configurable": {"thread_id": "thread1"}})
print(result["messages"][-1].content)
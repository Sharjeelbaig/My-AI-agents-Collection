from src.features.agent.agent import agent

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Create './My Document.pdf' to replace all of it's content with whole information about AI agents with extensive details, nice formatting and examples."
    }]
},
config={"configurable": {"thread_id": "test"}}
)
print(result)

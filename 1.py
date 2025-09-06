from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_ollama import OllamaLLM
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph
from langchain.output_parsers import PydanticOutputParser
import pydantic

from llm import llm

i = 0

class KoreanResponse(pydantic.BaseModel):
    definition: str = pydantic.Field(description="definition of the word, in english")
    examples: str = pydantic.Field(description="example sentence on how to use the word in a sentence")

parser = PydanticOutputParser(pydantic_object=KoreanResponse)



class ChatState(MessagesState):
    input: str


def ask_llm(state: ChatState):
    global i
    # import ipdb; ipdb.set_trace()
    # response = [AIMessage(content="Response")] + state["messages"]
    # response = llm.invoke(state["messages"])
    # prompt = [
    #     *state["messages"],
    #     HumanMessage(content=state["input"]),
    #     SystemMessage(
    #         content="You must always reply in Korean. You must not reply in English."
    #     ),
    # ]
    # messages = [*state["messages"], prompt]
    
    response = llm.invoke(prompt)
    # response = chain2.invoke(state["messages"])
    # import ipdb; ipdb.set_trace()
    # import ipdb;ipdb.set_trace()
    # response = AIMessage(
    #     content="This is a response",
    #     type="ai",
    #     response_metadata={},
    #     id=f"{i + 1}",
    #     name=None,
    # )

    i += 1

    # return {"messages": [response, *state["messages"]]}
    # return {"messages": [prompt, response]}
    # return {"messages": [prompt]}
    return {"messages": response}
    # return {}


def add_system(state: ChatState):
    return {
        "messages": SystemMessage(
            "You are a Korean tutor, helping the user learn Korean. You will explain what Korean words mean, and give example sentence to illustrate how the word is used in context."
        )
    }


def add_prompt(state: ChatState):
    return {"messages": HumanMessage(state["input"])}


def is_system_added(state: ChatState):
    return (len(state["messages"])) != 0
    # return {"messages": SystemMessage("Reply in korean.")}


graph = StateGraph(ChatState)
graph.add_node("start", lambda state: {"messages": []})
graph.add_node("add_system", add_system)
graph.add_node("add_prompt", add_prompt)
graph.add_node("llm", ask_llm)

graph.set_entry_point("start")
graph.set_finish_point("llm")

graph.add_conditional_edges(
    "start", is_system_added, {True: "add_prompt", False: "add_system"}
)
graph.add_edge("add_system", "add_prompt")
graph.add_edge("add_prompt", "llm")

# graph.add_node("start", add_system)
# graph.add_edge(START, "start")
# graph.set_entry_point("start")
# graph.set_finish_point("start")
memory = MemorySaver()
chain = graph.compile(checkpointer=memory)

while True:
    prompt = input("> ")
    if not prompt:
        continue
    response = chain.invoke(
        {"messages": [], "input": prompt},
        {"configurable": {"thread_id": "abc123"}},
    )
    # print(response["messages"][-1].content)
    # [print(r) for r in response["messages"]]
    response["messages"][-1].pretty_print()
    # print(response)
    # import ipdb;ipdb.set_trace()
    print("\n")

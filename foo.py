import sqlite3

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import MessagesState, StateGraph


# Create the checkpointer properly
def create_checkpointer():
    # Method 1: Using connection string
    return SqliteSaver.from_conn_string("conversation.db")  # or "chat.db"


# Or Method 2: Using existing connection
def create_checkpointer_with_conn():
    conn = sqlite3.connect("chat.db", check_same_thread=False)
    return SqliteSaver(conn)


llm = ChatOllama(model="llama3.1:8b")


def chat_node(state: MessagesState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


graph = StateGraph(MessagesState)
graph.add_node("chat", chat_node)
graph.set_entry_point("chat")
graph.set_finish_point("chat")

# Use the properly created checkpointer
checkpointer = create_checkpointer()
app = graph.compile(checkpointer=checkpointer)


def interactive_chat():
    config = {"configurable": {"thread_id": "test_conversation"}}

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break

        result = app.invoke(
            {"messages": [HumanMessage(content=user_input)]}, config=config
        )

        print(f"AI: {result['messages'][-1].content}")


interactive_chat()

from graph import graph
from llm import ollama_is_up
from util import trycatch
from langgraph.graph import MessagesState

features = 3


@trycatch
def main():
    ollama_is_up()
    print("What is your project idea?")
    while True:
        # prompt = input("> ")
        prompt = "I want to build an app to track my sleep."
        if not prompt:
            continue
        response:MessagesState = graph.invoke(prompt) # type: ignore
        response["messages"][-1].pretty_print()
        # import ipdb; ipdb.set_trace()
        # [print(r) for r in response["messages"]]
        # import ipdb;ipdb.set_trace()
        print("\n")
        break


if __name__ == "__main__":
    main()

import ipdb
from graph import ChatState, make_graph
from llm import ollama_is_up
from util import trycatch, logger
from langgraph.graph import MessagesState


@trycatch
def main():
    ollama_is_up()

    graph = make_graph(system_prompt="")

    print("What is your project idea?")
    prompts = [
        "I want to build an app to track my sleep.",
        "I want to use Svelte"
    ]
    prompts.reverse()
    while True:
        # prompt = input("> ")
        # prompt = "I want to build an app to track my sleep."
        if prompts:
            prompt = prompts.pop()
        else:
            prompt=input("> ")
        if not prompt:
            continue
        # c: ChatState = {"conversation_begun": False, "input": prompt, "messages": []}
        response:MessagesState = graph.invoke(prompt) # type: ignore
        logger.info(response["messages"][-1].content)
    
        print("\n")


if __name__ == "__main__":
    main()

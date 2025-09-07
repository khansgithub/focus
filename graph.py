import json
from types import MethodType
from typing import Any, Callable

import ipdb
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph

import util
from llm import SYSTEM_PROMPT, llm
from prompts import STAGE1, STAGE1_1
from util import Stage, YesNoResponse, logger

"""
 ENTRY
   │
   ▼
[start] 
   │ (conditional: next_stage)
   ├── 1 ──▶ [add_prompt] ──▶ [stage1] ──▶ END
   │
   ├── 1.1 ──▶ [stage1.1] 
   │
   └── 2 ──▶ [stage2] ──▶ END (finish point)
"""
THREAD_ID = "foobar"


MEMORY = MemorySaver()


class ChatState(MessagesState):
    input: str
    stage: Stage


def ask_llm(state: ChatState):
    logger.debug(state)
    import ipdb

    try:
        if is_first_msg(state):
            messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
            response = llm.invoke(messages)
            ...
        else:
            # logger.debug("invoking llm with")
            # for m in state["messages"]:
            #     m.pretty_print()
            response = llm.invoke(state["messages"])

        # line()
        # import ipdb; ipdb.set_trace()
        # logger.debug("invoking parser llm with")
        # logger.debug(response.content)
        # line()
        # parsed_response = parser_llm.invoke({"response_to_parse": response.content})
        return {"messages": response}
    except Exception as e:
        logger.exception(e)
        import ipdb

        ipdb.set_trace()
        raise e
    return {"messages": response}


def add_system(state: ChatState):
    return {"messages": SystemMessage(SYSTEM_PROMPT)}


def add_prompt(state: ChatState):
    return {"messages": HumanMessage(state["input"])}


def is_first_msg(state: ChatState):
    return len(state["messages"]) == 0


###########
# STAGE 0 #
###########
def stage0(state: ChatState):
    return {"messages": SystemMessage(content=STAGE1)}

###########
# STAGE 1 #
###########
def stage1(state: ChatState):
    messages = [SystemMessage(content=STAGE1), *state["messages"]]
    response = llm.invoke(messages)
    state["stage"].stage = 1
    return {"messages": response}


def stage1_1(state: ChatState):
    messages = [
        *state["messages"],
        SystemMessage(content=STAGE1_1),
        HumanMessage(state["input"]),
    ]
    response = llm.invoke(messages)
    state["stage"].stage = 1.1
    return {"messages": response}


###########
# STAGE 2 #
###########
def stage2(state):
    ipdb.set_trace()


def next_stage(state: ChatState) -> float:
    prev_stage = state["stage"].stage
    next_stage = 0

    if prev_stage == -1:
        next_stage = 0
    elif prev_stage == 0:
        next_stage = 1
    elif prev_stage == 1:
        # check if the user is okay with the stack
        yesno = llm_yes_no_parse(
            system_msg="""Respond with the following template: {"answer": <"YES"/"NO">""",
            q=f"""Does this response "{state['input']}" indicate agreement, or a difference in opinion?""",
        )
        next_stage = 2 if yesno.answer.lower() == "yes" else 1.1

    elif prev_stage == 1.1:
        q = "\n".join(
            [
                f"{m.type}:{m.content}"
                for m in state["messages"]
                if isinstance(m.content, str)
            ]
        )
        yesno = llm_yes_no_parse(
            system_msg="""
                Respond with the following template:
                "
                {{
                    "answer": <"YES" for agreement or "NO" disagreement>,
                    "reasoning": <put your reasoning here>
                }}
                "
            """,
            q=q,
        )
        next_stage = 2 if yesno.answer.lower() == "yes" else 2
    logger.debug(f"{next_stage=}")
    return next_stage


def llm_yes_no_parse(q: str, system_msg: str) -> YesNoResponse:
    logger.debug(q)
    logger.debug(system_msg)
    sys = SystemMessage(system_msg)
    response = llm.invoke([sys, HumanMessage(q)])
    try:
        if isinstance(response.content, str):
            json_data = json.loads(response.content.lower())
            logger.debug(json_data)
            return YesNoResponse(**json_data)
        else:
            raise Exception("Response is not a str")
    except Exception:
        ipdb.set_trace()
        raise Exception()


def overload_invoke(orig_invoke):
    def _invoke(self, prompt: str):
        state: ChatState = {"input": prompt, "messages": [], "stage": util.stage()}
        return orig_invoke(
            state,
            {"configurable": {"thread_id": THREAD_ID}},
        )

    return _invoke


def make_graph(
    system_prompt: str | None = None, first_msg_format: str | None = None
) -> CompiledStateGraph[ChatState, None, ChatState, ChatState]:
    global SYSTEM_PROMPT
    if system_prompt:
        SYSTEM_PROMPT = system_prompt
    graph: StateGraph[ChatState, None, ChatState, ChatState] = StateGraph(ChatState)
    nodes: list[tuple[str, Callable]] = [
        ("start", lambda state: {"messages": []}),
        ("stage0", stage0),
        ("stage1", stage1),
        ("stage1.1", stage1_1),
        ("stage2", stage2),
        ("add_system", add_system),
        ("add_prompt", add_prompt),
        ("llm", ask_llm),
    ]

    edges = [
        "add_prompt -> stage1"
    ]

    end_nodes = [node for [node, _] in nodes if node.startswith("stage")]

    for [name, f] in nodes:
        graph.add_node(name, f)

    for edge in edges:
        graph.add_edge(*edge.split(" -> "))

    graph.set_entry_point("start")

    for end_node in end_nodes:
        graph.add_edge(end_node, END)

    graph.add_conditional_edges(
        "start",
        next_stage,
        {0: "stage0", 1: "add_prompt", 1.1: "stage1.1", 2: "stage2"},
    )


    # graph.add_edge(START, "stage1")
    # graph.add_edge("add_system", "add_prompt")
    # graph.add_edge("add_prompt", "llm")
    r = graph.compile(checkpointer=MEMORY)
    r.invoke = MethodType(overload_invoke(r.invoke), graph)
    print(r.get_graph().print_ascii())
    input(" payuse > ")
    return r


graph = make_graph()

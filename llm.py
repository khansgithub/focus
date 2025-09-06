import json
import sys
from langchain.schema.runnable import RunnableLambda
from langchain_core.runnables.base import RunnableSequence, RunnableSerializable

from langchain.prompts import ChatPromptTemplate
from platform import architecture
import langchain
from langchain.chains.llm import LLMChain
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import httpcore
import httpx
from langchain_ollama import ChatOllama
from prompts import SYSTEM_PROMPT, PARSER_SYSTEM_PROMPT

from util import logger


MODEL = "llama3.1:8b"
FEATURES = 3
SYSTEM_PROMPT = SYSTEM_PROMPT.format(features=FEATURES)


def _parse_to_json(llm_output: AIMessage):
    import ipdb

    ipdb.set_trace()
    logger.info(llm_output.content)
    if not isinstance(llm_output.content, str):
        raise Exception("output.content is not a str, can't parse to json")

    is_json = False
    count: list[int] = []
    json_start = llm_output.content.find("{")
    json_end = llm_output.content.rfind("}")

    if json_start != -1 and json_end != -1:
        llm_output.content = json.loads(llm_output.content[json_start:json_end])
        logger.info(llm_output.content)

        return llm_output
    else:
        logger.debug("Coudln't parse json")
        import ipdb; ipdb.set_trace()

    return llm_output


def _parser_llm() -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                PARSER_SYSTEM_PROMPT,
            ),
            ("human", "{response_to_parse}"),
        ]
    )
    return prompt | llm | RunnableLambda(_parse_to_json)


def ollama_is_up() -> bool:
    try:
        ChatOllama(model=MODEL).invoke("")
    except (httpcore.ConnectError, httpx.ConnectError):
        logger.error("Ollama is not running")
        sys.exit(0)
        return False
    return True


llm = ChatOllama(model=MODEL)
parser_llm = None #_parser_llm()

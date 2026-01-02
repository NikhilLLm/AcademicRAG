from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv("C:/Users/nshej/aisearch/.env")

_DEFAULT_PROMPT_TEXT = """
You are an assistant tasked with summarizing tables and text.
Give a concise summary of the table or text.

Respond only with the summary, no additional comment.
Do not start your message by saying "Here is a summary".
Just give the summary as it is.

Table or text chunk: {element}
"""


def groq_llm(
    text: str,
    MODEL_NAME: str,
    max_token:int,
    temperature:float,
    prompt_template: ChatPromptTemplate | None = None,
) -> str:
    """
    Run Groq LLM with configurable model and prompt.
    """
    if not text or not text.strip():
        return ""

    model = ChatGroq(
        temperature=temperature,
        model=MODEL_NAME,
        max_tokens=max_token
    )

    if prompt_template is None:
        prompt = ChatPromptTemplate.from_template(_DEFAULT_PROMPT_TEXT)
    elif isinstance(prompt_template, ChatPromptTemplate):
        prompt = prompt_template
    else:
        prompt = ChatPromptTemplate.from_template(prompt_template)

    chain = (
        {"element": lambda x: x}
        | prompt
        | model
        | StrOutputParser()
    )

    return chain.invoke(text)

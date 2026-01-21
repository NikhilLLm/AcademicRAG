from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
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
    text,
    MODEL_NAME: str,
    max_token: int,
    temperature: float,
    prompt_template: PromptTemplate,
) -> str:
    """
    Universal Groq LLM runner that auto-maps inputs
    based on PromptTemplate.input_variables
    """

    if text is None:
        return ""

    model = ChatGroq(
        temperature=temperature,
        model=MODEL_NAME,
        max_tokens=max_token,
        
    )

    chain = prompt_template | model | StrOutputParser()

    expected_vars = prompt_template.input_variables

    # Case 1: Dict input (validation / repair)
    if isinstance(text, dict):
        missing = set(expected_vars) - set(text.keys())
        if missing:
            raise KeyError(f"Missing prompt variables: {missing}")
        return chain.invoke(text)

    # Case 2: String input (single-variable prompt)
    if isinstance(text, str):
        if len(expected_vars) != 1:
            raise ValueError(
                f"Prompt expects variables {expected_vars}, but received string input"
            )
        return chain.invoke({expected_vars[0]: text})

    raise TypeError("text must be str or dict")

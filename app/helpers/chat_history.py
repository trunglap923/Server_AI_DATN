from langchain_core.messages import trim_messages, BaseMessage
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

def custom_token_counter(messages: list[BaseMessage]) -> int:
    text_content = ""
    for msg in messages:
        if isinstance(msg.content, str):
            text_content += msg.content
        elif isinstance(msg.content, list):
            for part in msg.content:
                if isinstance(part, str):
                    text_content += part
                elif isinstance(part, dict) and 'text' in part:
                    text_content += part['text']

    return len(enc.encode(text_content))

def get_chat_history(messages, max_tokens=1000):
    return trim_messages(
        messages,
        max_tokens=max_tokens,
        strategy="last",
        token_counter=custom_token_counter,
        include_system=True,
        start_on="human",
        allow_partial=False
    )

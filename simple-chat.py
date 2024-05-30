import json
import logging
import os
import streamlit as st  # 1.34.0
import time
import tiktoken

from datetime import datetime
from openai import AzureOpenAI


logger = logging.getLogger()
logging.basicConfig(encoding="UTF-8", level=logging.INFO)

st.set_page_config(page_title="Streamlit Chat Interface Improvement",
                   page_icon="🤩")

st.title("🤩 Improved Streamlit Chat UI")

# Validates the Azure OpenAI Configuration
if "ai_config_validated" not in st.session_state:
    if os.getenv('AZURE_OPENAI_ENDPOINT') == "" and os.getenv('AZURE_OPENAI_API_KEY') == "" and os.getenv('AZURE_OPENAI_API_VERSION') == "" and os.getenv('AZURE_OPENAI_DEPLOYMENT') == "":
        st.stop("Please set the Azure OpenAI configuration variables")
    # print the Azure OpenAI Configuration
    print(f"AZURE_OPENAI_ENDPOINT = {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"AZURE_OPENAI_API_KEY = {os.getenv('AZURE_OPENAI_API_KEY')}")
    print(f"AZURE_OPENAI_API_VERSION = {os.getenv('AZURE_OPENAI_API_VERSION')}")
    print(f"AZURE_OPENAI_DEPLOYMENT = {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
    st.session_state["ai_config_validated"] = "OK"


client = AzureOpenAI(
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_key= os.getenv('AZURE_OPENAI_API_KEY'),
    azure_deployment= os.getenv('AZURE_OPENAI_DEPLOYMENT'),
    api_version= os.getenv('AZURE_OPENAI_API_VERSION')
   )

# This function logs the last question and answer in the chat messages
def log_feedback(icon):
    # We display a nice toast
    st.toast("Thanks for your feedback!", icon="👌")

    # We retrieve the last question and answer
    last_messages = json.dumps(st.session_state["messages"][-2:])

    # We record the timestamp
    activity = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": "

    # And include the messages
    activity += "positive" if icon == "👍" else "negative"
    activity += ": " + last_messages

    # And log everything
    logger.info(activity)


# Adapted from https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps
if "messages" not in st.session_state:
    st.session_state["messages"] = []

user_avatar = "👩‍💻"
assistant_avatar = "🤖"

# In case of rerun of the last question, we remove the last answer from st.session_state["messages"]
if "rerun" in st.session_state and st.session_state["rerun"]:

    st.session_state["messages"].pop(-1)

# We rebuild the previous conversation stored in st.session_state["messages"] with the corresponding emojis
for message in st.session_state["messages"]:
    with st.chat_message(
        message["role"],
        avatar=assistant_avatar if message["role"] == "assistant" else user_avatar,
    ):
        st.markdown(message["content"])

# A chat input will add the corresponding prompt to the st.session_state["messages"]
if prompt := st.chat_input("How can I help you?"):

    st.session_state["messages"].append({"role": "user", "content": prompt})

    # and display it in the chat history
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(prompt)

# If the prompt is initialized or if the user is asking for a rerun, we
# launch the chat completion by the LLM
if prompt or ("rerun" in st.session_state and st.session_state["rerun"]):

    with st.chat_message("assistant", avatar=assistant_avatar):
        stream = client.chat.completions.create(
            model=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["messages"]
            ],
            stream=True,
            #max_tokens=300,  # Limited to 300 tokens for demo purposes
        )
        response = st.write_stream(stream)
    st.session_state["messages"].append({"role": "assistant", "content": response})

    # In case this is a rerun, we set the "rerun" state back to False
    if "rerun" in st.session_state and st.session_state["rerun"]:
        st.session_state["rerun"] = False

# If there is at least one message in the chat, we display the options
if len(st.session_state["messages"]) > 0:

    # We set the space between the icons thanks to a share of 100
    cols_dimensions = [7, 19.4, 19.3, 9, 8.6, 8.6, 28.1]
    col0, col1, col2, col3, col4, col5, col6 = st.columns(cols_dimensions)

    with col1:

        # Converts the list of messages into a JSON Bytes format
        json_messages = json.dumps(st.session_state["messages"]).encode("utf-8")

        # And the corresponding Download button
        st.download_button(
            label="📥 Save chat!",
            data=json_messages,
            file_name="chat_conversation.json",
            mime="application/json",
        )

    with col2:

        # We set the message back to 0 and rerun the app
        # (this part could probably be improved with the cache option)
        if st.button("Clear Chat 🧹"):
            st.session_state["messages"] = []
            st.rerun()

    with col3:
        icon = "🔁"
        if st.button(icon):
            st.session_state["rerun"] = True
            st.rerun()

    with col4:
        icon = "👍"

        # The button will trigger the logging function
        if st.button(icon):
            log_feedback(icon)

    with col5:
        icon = "👎"

        # The button will trigger the logging function
        if st.button(icon):
            log_feedback(icon)

    with col6:

        # We initiate a tokenizer
        enc = tiktoken.get_encoding("cl100k_base")

        # We encode the messages
        tokenized_full_text = enc.encode(
            " ".join([item["content"] for item in st.session_state["messages"]])
        )

        # And display the corresponding number of tokens
        label = f"💬 {len(tokenized_full_text)} tokens"
        st.link_button(label, "https://platform.openai.com/tokenizer")

else:

    # At the first run of a session, we temporarly display a message
    if "disclaimer" not in st.session_state:
        with st.empty():
            for seconds in range(3):
                st.warning(
                    "You can click on 👍 or 👎 to provide feedback regarding the quality of responses.",
                    icon="💡",
                )
                time.sleep(1)
            st.write("")
            st.session_state["disclaimer"] = True
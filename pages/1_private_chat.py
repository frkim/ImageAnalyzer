import streamlit as st
import os

from langchain.agents import initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from dotenv import load_dotenv

from langchain.agents import load_tools, initialize_agent

tempImagefile = None

load_dotenv()


def get_azure_openai_client():
    client = AzureChatOpenAI(
        azure_endpoint = os.environ['AZURE_OPENAI_ENDPOINT'],
        azure_deployment = os.environ['AZURE_OPENAI_MODEL_NAME'],
        api_version = os.environ['AZURE_OPENAI_API_VERSION'],
        api_key = os.environ['AZURE_OPENAI_API_KEY'],
        temperature=0.0,
        streaming=True
    )

    return client

config = """
AZURE_OPENAI_ENDPOINT={AZURE_OPENAI_ENDPOINT}
AZURE_OPENAI_MODEL_NAME={AZURE_OPENAI_MODEL_NAME}
AZURE_OPENAI_API_VERSION={AZURE_OPENAI_API_VERSION}
AZURE_OPENAI_API_KEY={AZURE_OPENAI_API_KEY}
"""
config = config.format(AZURE_OPENAI_ENDPOINT= os.getenv('AZURE_OPENAI_ENDPOINT'), 
                       AZURE_OPENAI_MODEL_NAME= os.getenv('AZURE_OPENAI_MODEL_NAME'),
                       AZURE_OPENAI_API_VERSION= os.getenv('AZURE_OPENAI_API_VERSION'),
                       AZURE_OPENAI_API_KEY= os.getenv('AZURE_OPENAI_API_KEY')
                       )

with st.expander("Parameters"):
    st.code(config)


st.title("Private chat")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Salut, je suis un chatbot qui peut rechercher sur le web. Comment puis-je t'aider?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

systemPrompt = """
Vous devez répondre aux questions des utilisateurs en utilisant les outils à votre disposition.
        Ne faites pas de suppositions sur les valeurs à introduire dans les fonctions. Demandez des éclaircissements si la demande d'un utilisateur est ambiguë.
 Ne mettez pas de valeurs vides dans les fonctions. Ne répondez pas à des questions sans rapport avec le sujet. Répondez en priorité en français sauf si la demande est formulée en anglais"""

if prompt := st.chat_input(placeholder="Posez une question ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "system", "content": systemPrompt})
    st.chat_message("user").write(prompt)

    llm = get_azure_openai_client()
    tools = load_tools(["ddg-search"])
    search_agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, handle_parsing_errors=False, verbose=False)

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        response = search_agent.run(st.session_state.messages, callbacks=[st_cb])
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.messages.append({"role": "system", "content": systemPrompt})
        st.write(response)

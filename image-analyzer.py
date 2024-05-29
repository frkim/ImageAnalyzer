import streamlit as st
import os
import piexif
import tempfile
import base64
import toml

from PIL import Image

from openai import AzureOpenAI
import streamlit as st

from utils import extract_variables_and_set_env, mask_string, validates_AI_Parameters

tempImagefile = None
ai_configuration = None
ai_config_validated = None
config = None

if "ai_config_validated" in st.session_state:
    v = st.session_state["ai_config_validated"]


# Initialize Azure OpenAI Configuration from the environment variables or the AI Parameters textbox
def initialize_AI_configuration():
    if "ai_config_validated" not in st.session_state:
        if not validates_AI_Parameters():
            # OS environment variables are not set, try to set them from the AI parameters textbox
            if "ai_configuration" in st.session_state:
                ai_configuration = st.session_state["ai_configuration"]
                extract_variables_and_set_env(ai_configuration)
        if (validates_AI_Parameters()):
            st.session_state["ai_configuration_validated"] = "OK"
            print(f"AZURE_OPENAI_ENDPOINT = {os.getenv('AZURE_OPENAI_ENDPOINT')}")
            print(f"AZURE_OPENAI_API_KEY = {os.getenv('AZURE_OPENAI_API_KEY')}")
            print(f"AZURE_OPENAI_DEPLOYMENT = {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
            print(f"AZURE_OPENAI_API_VERSION = {os.getenv('AZURE_OPENAI_API_VERSION')}")
            st.session_state["ai_config_validated"] = "OK"
        else:
            st.write("Please set the Azure OpenAI OS environment variables or fill in the AI Parameters textbox with these values.")
            config = """AZURE_OPENAI_ENDPOINT={AZURE_OPENAI_ENDPOINT}
AZURE_OPENAI_API_KEY={AZURE_OPENAI_API_KEY}
AZURE_OPENAI_DEPLOYMENT={AZURE_OPENAI_DEPLOYMENT}
AZURE_OPENAI_API_VERSION={AZURE_OPENAI_API_VERSION}
"""
            st.code(config, line_numbers=50)

initialize_AI_configuration()

def get_azure_openai_client():
    client = AzureOpenAI(
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_key= os.getenv('AZURE_OPENAI_API_KEY'),
    azure_deployment= os.getenv('AZURE_OPENAI_DEPLOYMENT'),
    api_version= os.getenv('AZURE_OPENAI_API_VERSION')
   )
    return client


if "ai_config_validated" in st.session_state:
    config = """AZURE_OPENAI_ENDPOINT={AZURE_OPENAI_ENDPOINT}
AZURE_OPENAI_API_KEY={AZURE_OPENAI_API_KEY}
AZURE_OPENAI_DEPLOYMENT={AZURE_OPENAI_DEPLOYMENT}
AZURE_OPENAI_API_VERSION={AZURE_OPENAI_API_VERSION}
    """
    config = config.format(AZURE_OPENAI_ENDPOINT= os.getenv('AZURE_OPENAI_ENDPOINT'), 
                        AZURE_OPENAI_API_KEY= mask_string(os.getenv('AZURE_OPENAI_API_KEY')),
                        AZURE_OPENAI_DEPLOYMENT= os.getenv('AZURE_OPENAI_DEPLOYMENT'),
                        AZURE_OPENAI_API_VERSION= os.getenv('AZURE_OPENAI_API_VERSION')
                        )

with st.expander("AI Parameters"):
    ai_configuration = st.text_area("Azure OpenAI Parameters:", config, height=130)
    st.session_state["ai_configuration"] = ai_configuration

st.image("image_analyzer_logo.png", use_column_width=False)

system_prompt = "You are a helpful assistant which describes images"

# Validates the Global Configuration
if "global_config_validated" not in st.session_state:
    config_file = "config.toml"
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"No file found at {config_file}")
    with open(config_file, 'r', encoding='utf-8') as file:
        data = toml.load(file)
        system_prompt = data['image_analyzer']['system_prompt']
        st.session_state["system_prompt"] = system_prompt
    st.session_state["global_config_validated"] = "OK"
else:
    system_prompt = st.session_state["system_prompt"]

with st.expander("System Prompt"):
    system_prompt = st.text_area("Describe your system prompt here:", system_prompt, height=400)

st.title("Image Analyzer 📷🎯📑")

uploaded_file = st.file_uploader("Choose a JPG or PNG image file", type=['jpg', 'png'])

def process_image(image_path, st):
    description = ""
    client = AzureOpenAI(
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_key= os.getenv('AZURE_OPENAI_API_KEY'),
    azure_deployment= os.getenv('AZURE_OPENAI_DEPLOYMENT'),
    api_version= os.getenv('AZURE_OPENAI_API_VERSION')
    )

    base_64_encoded_image = base64.b64encode(open(image_path, "rb").read()).decode(
        "ascii"
    )
    image_url = f"data:image/jpeg;base64,{base_64_encoded_image}"

    with st.spinner('Traitement en cours...'):
        response = client.chat.completions.create(
            model= os.getenv('AZURE_OPENAI_DEPLOYMENT'),
            messages=[
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": [  
                    { 
                        "type": "text", 
                        "text": "Describe this picture" 
                    },
                    { 
                        "type": "image_url",
                        "image_url": {
                            "url": f"{image_url}"
                        }
                    }
                ] } 
            ],
            max_tokens=2000 
        )
    st.success('Terminé !')

    description = response.choices[0].message.content
    return description

if uploaded_file is not None:
    tempImagefile = tempfile.NamedTemporaryFile(delete=False) 

    tempImagefile.write(uploaded_file.getvalue())
    image = Image.open(uploaded_file)
    st.image(image, caption='', use_column_width=True)
   
    exif_data = None
    if uploaded_file.type == 'image/jpeg':
        exif_data = piexif.load(image.info["exif"])
        with st.expander("Metadata"):
            st.write("", exif_data)

    image_analysis = process_image(tempImagefile.name, st) 
    if (image_analysis is set):
        st.session_state.messages.append({"role": "assistant", "content": image_analysis})

    st.text_area("Description", image_analysis, height=200)


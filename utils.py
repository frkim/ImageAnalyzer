import os


def validates_AI_Parameters():
    """
    Validates the required environment variables for AI parameters.

    Returns:
        bool: True if all required environment variables are set, False otherwise.
    """
    return (os.getenv('AZURE_OPENAI_ENDPOINT') is not None and
            os.getenv('AZURE_OPENAI_API_KEY') is not None and
            os.getenv('AZURE_OPENAI_API_VERSION') is not None and
            os.getenv('AZURE_OPENAI_DEPLOYMENT') is not None)

def extract_variables_and_set_env(env_variable_string):
    """
    Extracts variables from a string in the format "var_name=var_value" and sets them as environment variables.

    Args:
        env_variable_string (str): A string containing environment variable assignments in the format "var_name=var_value".

    Returns:
        None
    """
    if (env_variable_string is None or env_variable_string == ""):
        return
    lines = env_variable_string.strip().split("\n")
    for line in lines:
        line = line.strip()
        try:
            var_name, var_value = line.split("=")
            var_value = var_value.strip().strip('"')
            os.environ[var_name.strip()] = var_value
        except Exception as e:
            print(f"Error setting environment variable: {e}")


def mask_string(s):
    """
    Masks the input string by replacing all characters except the last 4 with asterisks.

    Args:
        s (str): The input string to be masked.

    Returns:
        str: The masked string with asterisks replacing all characters except the last 4.
    """
    return '*' * (len(s) - 4) + s[-4:]
import os

def get_env(var, default=None):
    return os.environ[var] or default

# Check if environment variable PYTHON_ENV is set

if "PYTHON_ENV" in os.environ:
    pass

config = {
    'env': get_env('PYTHON_ENV')
}
from setuptools import setup, find_packages

setup(
    name="openmanus-x",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "google-genai"
    ],
    entry_points={
        "console_scripts": [
            "omx=main:run_from_cli" # Updated to point to a standard entry function
        ]
    }

)

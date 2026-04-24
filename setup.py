from setuptools import find_packages, setup

setup(
    name="openmanus-x",
    version="0.3.0",
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=[
        "google-genai>=1.0.0",
        "python-dotenv>=1.0.0",
        "ddgs>=9.0.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "omx=core.cli:run_from_cli",
        ],
    },
    python_requires=">=3.10",
)

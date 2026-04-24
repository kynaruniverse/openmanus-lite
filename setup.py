from setuptools import find_packages, setup

setup(
    name="openmanus-x",
    version="0.4.0",
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    package_data={"web": ["static/*"]},
    install_requires=[
        "google-genai>=1.0.0",
        "python-dotenv>=1.0.0",
        "ddgs>=9.0.0",
        "fastapi>=0.110.0",
        "uvicorn[standard]>=0.27.0",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.30.0"],
        "all": ["openai>=1.0.0", "anthropic>=0.30.0"],
        "dev": ["pytest>=7.0", "pyinstaller>=6.0"],
    },
    entry_points={
        "console_scripts": [
            "omx=core.cli:run_from_cli",
            "omx-web=core.cli:run_web",
        ],
    },
    python_requires=">=3.10",
)

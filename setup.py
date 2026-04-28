from setuptools import setup, find_packages

setup(
    name="powerbi-mcp-server",
    version="1.0.0",
    description="Servidor MCP para interactuar con Power BI desde GitHub Copilot",
    author="Tu Nombre",
    packages=find_packages(),
    install_requires=[
        "mcp>=0.1.0",
        "pyadomd>=0.1.1",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "powerbi-mcp=src.server:main",
        ],
    },
    python_requires=">=3.10",
)

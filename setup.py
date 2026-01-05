from setuptools import setup, find_packages

setup(
    name="codinzhub-sprint-guardian",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "requests>=2.28.0",
        "tabulate>=0.9.0",
        "python-dateutil>=2.8.2",
    ],
    entry_points={
        "console_scripts": [
            "sprint-guardian=sprint_guardian.cli:main",
            "sprint-guardian-mcp=sprint_guardian.mcp_server:main",
        ],
    },
)

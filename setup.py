from setuptools import find_packages, setup


setup(
    name="dingtalk-cli",
    version="1.0.0",
    description="Agent-friendly CLI and built-in skill for DingTalk docs and wiki operations.",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="OpenAI Codex",
    python_requires=">=3.10",
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "prompt-toolkit>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dingtalk-cli=dingtalk_cli.cli:main",
        ],
    },
    package_data={
        "dingtalk_cli": ["skills/*.md"],
    },
    include_package_data=True,
    zip_safe=False,
)

from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).resolve().parent
ABOUT: dict[str, str] = {}
exec((ROOT / "dingtalk_cli" / "__init__.py").read_text(encoding="utf-8"), ABOUT)


setup(
    name="dingtalk-cli",
    version=ABOUT["__version__"],
    description="Agent-friendly CLI and built-in skill for DingTalk docs and wiki operations.",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="dingtalk-cli contributors",
    license="MIT",
    keywords="dingtalk cli agents wiki documents workbook",
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
            "build>=1.0.0",
            "twine>=5.0.0",
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
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)

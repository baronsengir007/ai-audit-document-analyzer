from setuptools import setup, find_packages

setup(
    name="ai_audit_scanner",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyPDF2",
        "python-docx",
        "openpyxl",
        "pandas",
        "pyyaml",
    ],
    python_requires=">=3.10",
) 
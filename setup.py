from setuptools import setup, find_packages

setup(
    name="agentvector",
    version="0.0.1",
    author="Shashi Jagtap",
    author_email="shashi@super-agentic.ai",
    description="AgentVector: The Cognitive Core for Your AI Agents. A lightweight, embeddable vector database for Agentic AI systems, built on LanceDB.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/superagenticai/agentvector",
    project_urls={
        "Homepage": "https://github.com/superagenticai/agentvector",
        "Repository": "https://github.com/superagenticai/agentvector",
    },
    packages=find_packages(exclude=["docs.*", "docs", "examples.*", "examples", "tests.*", "tests"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Database",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "lancedb>=0.6.0",
        "pydantic>=2.0",
        "numpy",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov",
            "pytest-asyncio",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    license="Apache License 2.0",
)
from setuptools import find_packages, setup

# Read the contents of the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="SQLAlchemy-ViewORM",
    version="0.1.0",
    author="AivanF.",
    author_email="fouren.aivan@gmail.com",
    description="A flexible ORM extension for defining and managing views (including materialized ones) in SQLAlchemy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AivanF/SQLAlchemy-ViewORM",
    packages=find_packages(),
    package_data={
        "sqlalchemy_view_orm": ["py.typed"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    python_requires=">=3.9",
    install_requires=[
        "sqlalchemy>=2.0.0",
    ],
    keywords="sqlalchemy, database, views, materialized views, orm",
    project_urls={
        "Bug Reports": "https://github.com/AivanF/SQLAlchemy-ViewORM/issues",
        "Source": "https://github.com/AivanF/SQLAlchemy-ViewORM",
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
            "pre-commit>=3.0.0",
        ],
    },
)

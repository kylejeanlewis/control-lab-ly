from setuptools import setup, find_packages
# import os

# here = os.path.abspath(os.path.dirname(__file__))
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

VERSION = '0.1.3'
DESCRIPTION = 'Lab Equipment Automation Package'
LONG_DESCRIPTION = 'A package that enables flexible automation and reconfigurable setups for high-throughput experimentation and machine learning'

# Setting up
setup(
    name="control-lab-le",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Chang Jie Leong",
    author_email="<changjie.leong@outlook.com>",
    url="https://github.com/kylejeanlewis/control-lab-le",
    
    py_modules=[],
    package_dir={"": "controllable"},
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas"
    ],
    extras_require = {
        "dev": [
            "pytest>=3.7",
        ],
    },
    
    keywords=['python', 'lab automation'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: Microsoft :: Windows",
    ]
)
from setuptools import setup, find_packages
# import os

# here = os.path.abspath(os.path.dirname(__file__))
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

VERSION = '0.1.3.4'
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
    
    packages=find_packages(where='src'),
    package_dir={"": "src"},
    setup_requires=['wheel'],
    package_data={'': ['*.json', '*.yaml']},
    include_package_data=True,
    install_requires=[
        "dash>=2.7",
        "impedance>=1.4",
        "imutils>=0.5",
        "matplotlib>=3.3",
        "nest_asyncio>=1.5",
        "numpy>=1.19",
        "pandas>=1.2",
        "plotly>=5.3",
        "pyModbusTCP>=0.2",
        "pyserial>=3.5",
        "PySimpleGUI",
        "PyVISA>=1.12",
        "PyYAML",
        "scipy>=1.6",
    ],
    # py_modules=[],
    # packages=find_packages(),
    # extras_require = {
    #     "dev": [
    #         "pytest>=3.7",
    #     ],
    # },
    
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
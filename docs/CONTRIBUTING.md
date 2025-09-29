# Contributing to Control-lab-ly

Thank you for considering contributing to the Control-lab-ly project! We welcome contributions of all kinds, including bug fixes, new features, documentation improvements, and more. This document outlines the guidelines and best practices for contributing to ensure a smooth and collaborative process.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
   - [Reporting Issues](#reporting-issues)
   - [Submitting Code Changes](#submitting-code-changes)
   - [Improving Documentation](#improving-documentation)
4. [Code Style Guidelines](#code-style-guidelines)
5. [Testing Your Changes](#testing-your-changes)
6. [Pull Request Process](#pull-request-process)

---

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

---

## Getting Started

1. **Fork the Repository**: Create a fork of the repository on GitHub.
2. **Clone Your Fork**: Clone your fork to your local machine:
   ```bash
   git clone https://github.com/[your-username]/control-lab-ly.git
   ```
3. **Set Up the Environment**:
   - Install the required dependencies:
     ```bash
     pip install -r dev/requirements_all.txt dev/requirements_dev.txt
     ```
   - For documentation contributions, install additional dependencies:
     ```bash
     pip install -r requirements_docs.txt
     ```
4. **Create a Branch**: Create a new branch for your changes:
   ```bash
   git checkout -b feature/[your-feature-name]
   ```

---

## How to Contribute

### Reporting Issues

If you encounter a bug or have a feature request, please open an issue on GitHub. Include the following:
- A clear and descriptive title.
- Steps to reproduce the issue (if applicable).
- Expected and actual behavior.
- Any relevant logs, screenshots, or code snippets.

### Submitting Code Changes

1. Follow the [Code Style Guidelines](#code-style-guidelines).
2. Ensure your changes are well-documented.
3. Write tests for your changes (if applicable).
4. Commit your changes with a descriptive message:
   ```bash
   git commit -m "Add feature: description of the feature"
   ```
5. Push your branch to your fork:
   ```bash
   git push origin feature/[your-feature-name]
   ```
6. Open a pull request (PR) on the main repository.

### Improving Documentation

We value clear and comprehensive documentation. To contribute:
- Add docstrings directly into the classes, methods, and functions you write, using [Google Style Python Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- Update or add content in the `docs/` folder.
- Follow the existing style and structure of the documentation.
- Use Markdown for text-based documentation.
- Preview your changes locally using `mkdocs`:
  ```bash
  mkdocs serve
  ```

---

## Code Style Guidelines
*To be updated*
<!-- - **Python Version**: Ensure compatibility with Python 3.10+.
- **Linting**: Use `flake8` to check for style issues:
  ```bash
  flake8 controllably/ tests/
  ```
- **Type Checking**: Use `mypy` for static type checking:
  ```bash
  mypy controllably/
  ```
- **Formatting**: Use `black` for code formatting:
  ```bash
  black controllably/ tests/
  ```
- **Imports**: Organize imports using `isort`:
  ```bash
  isort controllably/ tests/
  ``` -->

---

## Testing Your Changes

1. Write unit tests for your changes in the `tests/` directory.
2. Run the test suite using `tox`:
   ```bash
   tox
   ```
   This will automatically create isolated environments and run `pytest` in each environment specified in the `tox.ini` file.
3. To run tests for a specific environment, use:
   ```bash
   tox -e py310
   ```
   Replace `py310` with the desired environment.
4. Ensure all tests pass before submitting your changes.

---

## Pull Request Process

1. Ensure your branch is up-to-date with the `dev-v2-x-x` branch (appropriate upcoming version number):
   ```bash
   git fetch upstream
   git merge upstream/dev-v2-x-x
   ```
2. Address any merge conflicts.
3. Provide a clear and concise description of your changes in the PR.
4. Link any related issues in the PR description.
5. Wait for a review from the maintainers.
6. Address any feedback provided during the review process.

---

Thank you for contributing to Control-lab-ly! Your efforts help make this project better for everyone.
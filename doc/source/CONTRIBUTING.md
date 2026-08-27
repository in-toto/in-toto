# Contribute

Thank you for your interest in contributing to in-toto! We welcome contributions from the community to help improve and enhance the project.

## Quick Start Guide

To get started with contributing to in-toto, follow these steps:

### 1. Clone the Repository

Clone the in-toto git repository to your local machine:

```sh
git clone https://github.com/in-toto/in-toto.git
```

### 2. Install Development Dependencies

Navigate to the project root directory and install development dependencies using pip
(using [venv](https://docs.python.org/3/library/venv.html) is recommended):

```sh
pip install -r requirements-dev.txt
```

### 3. Review Contribution Guidelines

Before contributing, please review our [contribution guidelines](https://github.com/in-toto/community/blob/main/CONTRIBUTING.md) to ensure that your code follows our style guidelines and is properly tested.

### 4. Sign the Developer Certificate of Origin (DCO)

All contributors must sign the Developer Certificate of Origin (DCO) by adding a "Signed-off-by" line to their commit messages. This indicates your acceptance of the DCO. You can do this by appending the following line to each commit message (see [git commit --signoff](https://git-scm.com/docs/git-commit#Documentation/git-commit.txt---signoff)):

```sh
git commit -s -m "Your descriptive commit message"
```

### 5. Run Tests

Run the test suite using tox to ensure that your changes do not introduce any regressions:

```sh
tox 
```

This will execute the entire test suite in a separate virtual environment for each supported Python version.

#### Manual Testing

You can also run individual tests or the test suite manually if needed:

```sh
# Run individual tests
python <test_file.py>

# Run entire test suite
python runtests.py
```

#### Code Formatting

Ensure that your code follows the required formatting standards by using ruff:

```sh
# Apply ruff linter rules, isort rules will sort imports
ruff check

# Auto-format code with ruff
ruff format
```

#### Build Documentation

If you make changes to the documentation, build the HTML documentation locally:

```sh
cd doc && make html
```

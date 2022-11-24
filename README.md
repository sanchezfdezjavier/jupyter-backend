# Python Development Environment

![Tests](https://github.com/sanchezfdezjavier/python-testing-dev-env/actions/workflows/tests.yml/badge.svg)

## Usage

### Set up a Python virtual environment

1. Create the virtual environment

```bash
virtualenv venv
```

2. Source the your new virtual environment

```bash
source venv/bin/activate
```

1. Install tox with pip

```bash
pip3 install tox
```

### Run your tests

For running the **full suit**:

```bash
tox
```

For running **linting** analysis

```bash
tox -e lint
```

For running **static** analysis

```bash
tox -e static
```

For running **unit** tests

```bash
tox -e unit
```

For running **integration** tests

```bash
tox -e integration
```

## GitHub CI

Tests will automatically run on Pull Request.

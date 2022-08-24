# GroMEt2SMTLib


### Development Setup: Ubuntu 20.04
```bash
# install python 3.9
sudo apt install python3.9 python3.9-dev
# install dev dependencies
sudo apt install make
pip install --user pipenv
# install pygraphviz dependencies
sudo apt install graphviz libgraphviz-dev pkg-config
# Initialize development environment
make setup-dev-env
```

### Development Setup: OSX M1

```bash
# install python 3.9
brew install python3.9 python3.9-dev
# install dev dependencies
brew install make
pip install --user pipenv
# install pygraphviz dependencies
brew install graphviz libgraphviz-dev pkg-config
# install z3 
brew install z3
# Initialize development environment
make setup-dev-env
```


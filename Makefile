PIPENV=PIPENV_VENV_IN_PROJECT=1 pipenv

.PHONY: setup-dev-env destroy-dev-env
setup-dev-env:
	# Initializing virtual environment
	$(PIPENV) install --dev
	# Installing Z3
	$(PIPENV) run pysmt-install --z3 \
		--confirm-agreement \
		--install-path ./.smt-solvers
	$(PIPENV) run pysmt-install --check

destroy-dev-env:
	$(PIPENV) --rm

PY ?= python
export PYTHONPATH := src

.PHONY: all single mc figures test crosscheck

all: single mc figures

single:       ## one simulated panel: results/single_run.json, results/event_study.csv
	$(PY) -m staggered_did.run single

mc:           ## Monte Carlo study: results/montecarlo*.csv
	$(PY) -m staggered_did.run mc

figures:      ## fig/fig1_did.svg from the Monte Carlo results
	$(PY) -m staggered_did.figures

test:
	$(PY) -m pytest -q tests

crosscheck: single  ## compare with the R `did` package (Docker)
	docker build -q --platform linux/amd64 -t staggered-did-check checks
	docker run --rm --platform linux/amd64 -v "$(CURDIR)":/w -w /w staggered-did-check Rscript checks/did_crosscheck.R

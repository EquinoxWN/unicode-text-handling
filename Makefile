# OSV-Scanner (https://google.github.io/osv-scanner/) checks every resolved Maven dependency.
OSV ?= osv-scanner

.PHONY: setup lint test vectors report samples bench audit ci

setup:
	cd python && python -m pip install --upgrade pip && python -m pip install -e ".[dev]"

# Vectors up to date with the pinned Unicode files (downloads them once into data/), then each language.
lint:
	python spec/generate_vectors.py --check
	cd java && mvn -B -q -DskipTests compile
	cd python && python -m ruff check . ../spec && python -m ruff format --check . ../spec && python -m mypy
	cd js && npm run -s lint

# Shared Unicode 15.0.0 vectors, encoding samples and mojibake cases in Java, Python and JavaScript.
test:
	cd java && mvn -B -q verify
	cd python && python -m pytest -q
	cd js && npm test

# Rebuild spec/vectors and the Python grapheme table from data/ucd/15.0.0.
vectors:
	python spec/generate_vectors.py

# How each language's default APIs score on the shared vectors (tab-separated).
report:
	cd java && mvn -B -q -DskipTests compile && java -cp target/classes portfolio.unicodetexthandling.App report
	cd python && python -m unicode_text_handling report
	cd js && node src/cli.js report

# Byte, UTF-16, code point and grapheme counts of the shared samples, per language.
samples:
	cd java && java -cp target/classes portfolio.unicodetexthandling.App samples
	cd python && python -m unicode_text_handling samples
	cd js && node src/cli.js samples

bench:
	@echo "M2/M3: normalization and collation speed per language lands with the ICU work"

# Known vulnerabilities in Python, npm and Maven dependencies.
audit:
	cd python && python -m pip_audit --skip-editable --cache-dir ../.tmp/pip-audit
	cd js && npm audit
	cd java && mvn -B -q org.cyclonedx:cyclonedx-maven-plugin:2.9.3:makeAggregateBom -DoutputFormat=json -DoutputName=bom -DincludeTestScope=true
	$(OSV) scan source -L java/target/bom.json

ci: setup lint test report

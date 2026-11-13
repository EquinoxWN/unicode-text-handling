# unicode-text-handling (Python)

Python part of [unicode-text-handling](../README.md): an extended grapheme cluster segmenter
(UAX #29, Unicode 15.0.0), string length measurement, mojibake repair and the conformance runner.

```bash
pip install -e ".[dev]"
python -m unicode_text_handling measure "José"
python -m unicode_text_handling repair "JosÃ©"
python -m unicode_text_handling report    # needs ../spec/vectors (or --vectors DIR)
pytest -q
```

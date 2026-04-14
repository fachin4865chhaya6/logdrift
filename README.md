# logdrift

A lightweight CLI tool that tails and filters structured log files with regex and JSON path support.

---

## Installation

```bash
pip install logdrift
```

Or install from source:

```bash
git clone https://github.com/yourname/logdrift.git
cd logdrift
pip install .
```

---

## Usage

Tail a log file and filter by a regex pattern:

```bash
logdrift tail app.log --pattern "ERROR|WARN"
```

Filter structured JSON logs using a JSON path expression:

```bash
logdrift tail app.log --jsonpath "$.level" --value "error"
```

Combine both for precise filtering:

```bash
logdrift tail app.log --pattern "timeout" --jsonpath "$.service" --value "auth"
```

### Options

| Flag | Description |
|-------------|--------------------------------------|
| `--pattern` | Regex pattern to match log lines |
| `--jsonpath` | JSON path expression to extract field |
| `--value` | Expected value for the JSON path field |
| `--follow` | Continuously follow the log file |
| `--lines` | Number of lines to show from the end |

---

## Requirements

- Python 3.8+
- `jsonpath-ng`
- `click`

---

## License

This project is licensed under the [MIT License](LICENSE).
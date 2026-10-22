# Compliance Copilot CLI

Command-line interface for [Compliance Copilot](https://compliance.conmob.t-systems.net) — manage compliance rules, search your rule library directly from the terminal.

## Installation

```bash
pip install git+https://github.com/Ollsoft-ai/copilot-cli.git
```

Requires Python 3.11 or higher.

## Getting Started

```bash
compliance login
compliance init
```

`login` opens a browser window for authentication and saves a long-lived token locally. `init` downloads your company's compliance rules into the current project directory.

The CLI talks to https://compliance.conmob.t-systems.net. To use another instance, set `COMPLIANCE_SERVER_URL` (and `COMPLIANCE_FRONTEND_URL` if the web app lives elsewhere), e.g. `COMPLIANCE_SERVER_URL=https://compliance.ollsoft.org compliance login`.

## Commands

| Command | Description |
|---|---|
| `login` | Log in via browser and save credentials locally. |
| `logout` | Log out and remove saved credentials. |
| `switch` | Switch the active company without re-logging in. |
| `init` | Download compliance rules into the current project. |
| `update` | Update compliance rules, overwriting existing files. |
| `search-rules` | Search rules by keyword or meaning. |
| `tags` | List all unique tags across active rules. |
| `keywords` | List all unique keywords across active rules. |

## Usage Examples

```bash
# Search rules by free text
compliance search-rules "verify firmware signature"

# Filter by tag and severity
compliance search-rules --flags gdpr,logging --severity HIGH
```
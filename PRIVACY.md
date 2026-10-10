# Privacy Policy

The Finance Database, its Python package and its MCP server are free to use. There are no accounts, no API keys, no cookies, no advertising and no tracking, and nothing you send is sold or shared. This policy explains what little data is involved.

## The database

The database contains publicly available information about listed securities and their issuers, such as names, classifications, exchanges, identifiers and company headquarters. It contains no information about the people who use it.

## The Python package and the local MCP server

When you use the `financedatabase` package, or run the MCP server on your own computer, everything runs on your machine. The package downloads the database files from GitHub (`raw.githubusercontent.com`) and checks them for updates at most once a day; that request is subject to [GitHub's privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement). Nothing is sent anywhere else and no usage statistics are collected.

## The hosted MCP server

The hosted server at `https://financedatabase.jeroenbouma.com/mcp` answers the tool calls of your AI assistant.

- **What it receives:** the name of the tool and its arguments, for example a country or sector filter or a ticker to search for. It does not receive your conversation or any other content from your assistant; what your assistant does with your conversation is covered by its provider's own privacy policy.
- **Logs:** the server keeps standard technical logs of requests (time, path and response status) and, when a tool call fails, the error message, which can include the filter value that caused it. They are used only to keep the server running and to fix problems.
- **Usage statistics:** the server counts how often each tool is called per day, how often calls fail and how long they take. These totals are published at [`/stats`](https://financedatabase.jeroenbouma.com/stats). They contain no arguments, IP addresses or other information about who made a call.
- **Network:** requests reach the server through Cloudflare, which processes them (including your IP address) as described in [Cloudflare's privacy policy](https://www.cloudflare.com/privacypolicy/).

## Contact

Questions about this policy can be sent to jer.bouma@gmail.com.

_Last updated: October 10, 2026_

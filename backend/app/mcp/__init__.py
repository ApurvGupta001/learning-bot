"""MCP client layer + registry.

The agent loop never talks to a specific MCP server. It asks a `Retriever` for
docs relevant to a topic; the registry + factory decide which server(s) back it.
This indirection is the scalability seam: new MCP servers are added as registry
rows/config, not code changes.
"""

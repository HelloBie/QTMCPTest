import jsonschema

# hello tool's inputSchema
hello_schema = {
    "type": "object",
    "properties": {},
    "required": [],
}

# Test with empty dict
try:
    jsonschema.validate(instance={}, schema=hello_schema)
    print("hello schema + {} -> PASS")
except jsonschema.ValidationError as e:
    print(f"hello schema + empty dict -> FAIL: {e.message}")

# Test query schema
query_schema = {
    "type": "object",
    "properties": {
        "queryText": {"type": "string"},
        "keyword": {"type": "string"},
    },
    "required": ["queryText", "keyword"],
}

try:
    jsonschema.validate(instance={}, schema=query_schema)
    print("query schema + {} -> PASS")
except jsonschema.ValidationError as e:
    print(f"query schema + empty dict -> FAIL: {e.message}")

try:
    jsonschema.validate(instance={"queryText": "hello", "keyword": "greeting"}, schema=query_schema)
    print("query schema + valid args -> PASS")
except jsonschema.ValidationError as e:
    print(f"query schema + valid args -> FAIL: {e.message}")

# Simulate SDK behavior
print("\n--- SDK behavior ---")
print(f"None or {{}}: {None or {}}")

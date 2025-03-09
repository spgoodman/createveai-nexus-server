#!/bin/bash
curl "http://localhost:43080/api/openapi.json" -H "Authorization: Bearer sk-apiservertest1" | python -m json.tool

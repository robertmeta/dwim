# DWIM 

The **D**o **W**hat **I** **M**ean shell.

## Quickstart

- ```python3 -m venv .venv````
- ```source .venv/bin/activate```
- ```pip install -r requirements.txt```
- ```./dwim```

## Purpose

This is just a random experiment to see how reliable an LLM could be as an 
interface to a shell. Don't expect it to be worked on too often.

## Files

- README.md: this file 
- dwim: shell wrapper around the python
- main.py: the core python file
- requirements.txt: the python deps
- system.j2: the jinja2 prompt template for system setup
- user.j2: the jinja2 prompt template for system setup

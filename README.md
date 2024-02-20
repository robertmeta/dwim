# DWIM 

The **D**o **W**hat **I** **M**ean shell.

<iframe width="961" height="508" src="https://www.youtube.com/embed/IHTO8HOs_CM" title="DWIM Shell Demo" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## Quickstart

- ```python3 -m venv .venv```
- ```source .venv/bin/activate```
- ```pip install -r requirements.txt```
- ```./dwim```

## TODO

- [ ] Working tab complete 
- [ ] Error on missing OpenAI Key
- [ ] Anthropic support

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

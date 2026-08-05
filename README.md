# SciFlawBench Harness

## descriptions
This repository is mean to be a harness from which to run the sciflaw benchmark for models within an agentic context at the university of Bonn. It is built on top of smolagents and has a multiprocess architechture to allow for **blazingly** fast running of the benchmark

## code repository overview

```
src/
├── core/
│   ├── config.py               # base types used for parsing the config (w/ pydantic)
│   ├── events.py               # defines event watchers and base event primitives
│   ├── manager.py              # runtime manager code that handles dispatching subprocesses
│   ├── registry.py             # registry code which is reused for agent and tool registry (handles mapping string -> obj factory)
│   └── tasks.py                # definition for task primiteves and contains teh run_task function used for actual task runs
├── agents/
│   ├── prompts/
│   │   └── default.yaml        # defailt prompt associated wiht default agent
│   ├── prompts.py              # right now just containes a load prompt file
│   ├── definitions.py          # definitions of base agents to be used in testing and agent registry
│   └── base.py                 # contains build_agent function
├── models/
│   └── base.py                 # defines how to build a model and model wrapper
├── tools/
│   ├── definitions.py          # all custom tool definitions and wrapper/registry definiotion for use in pipeline
│   └── base.py                 # containes wrapper for use on all tools 
└── main.py                     # main entrypoint for running testing harness
```

## how to use

1. clone the repository and cd in
```bash 
git clone git@github.com:ivzx04/SciFlawBenchHarness.git && cd SciFlawBenchHarness
```
2. pip install the enviornment
```bash 
pip install -e .
```
3. Write the config file in config.json with your specific model access credentials
4. export the api key environment variable 
5. run src/main.py with your config path
```bash
python src/main.py --config /path/to/your/config
```

## TODOS (in order of importance): 

1.  need example tasks to ensure there are no larger scale problems with this architecture
2.  Evaluation logic needs to be done
    - Quantitatively: pattern would be add a new registry for validators and specify a list for given tasks
    - Qualitatively:  perhaps run a secondary pass on the result file objects dumped by the evaluator and parse
      according to the rubric
3.  more live integration tests would be nice
4.  build agent needs to support for multiagentic setups (some of this has been thougt out with parent child architecture)
5.  perhaps rethink how wrappers are made and what information we collect
6.  make better readme 


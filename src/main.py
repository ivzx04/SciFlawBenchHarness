from core.manager import RuntimeManager
from core.config import RunConfig

import json
import logging
from pathlib import Path

import click
from pydantic import ValidationError

logger = logging.getLogger(__file__)

@click.command()
@click.option('config', '--config', type=click.Path(), required=True, 
              help="specify the path to the configuration directory")
def main(config):
    """
    entry point for running the actual benchmark with a specific config file  
    """
    conf_path = Path(config)

    with open(conf_path, 'r') as f:
        raw = json.load(f)

    try: 
        conf = RunConfig(**raw)
    except ValidationError as e:
        logger.error(f"invalid configuration provided: {e}")
        raise

    manager = RuntimeManager(conf)
    manager.run()

if __name__ == "__main__":
    main()


import json
import os
import time

from .logger import logger


class StaticSimulation:  # pylint: disable=R0903
    """Data class for static Hoverfly simulation files

    :list file: list of files that are used in the simulation
    :list block_domains: list of domains (or domain glob patterns) for which simulations will be generated to
        block requests to.
    """

    file_type = "static"
    max_age = None  # Static simulations have no expiry

    def __init__(self, files: list = None, block_domains: list = (), capture_config=None):
        self.files = files if files else []
        self.block_domains = block_domains
        self.capture_config = capture_config
        self.file_paths = [os.path.join(self.file_type, file) for file in self.files]

    def full_file_path(self, data_dir, admin_port):
        # Specifying one static simulation that doesn't exist implies we want to record it once, then use it.
        if len(self.file_paths) == 1:
            return os.path.join(data_dir, "static", self.files[0])

        # pre-loaded simulations are modularised into multiple simulations, so need to be glommed into one for hoverfly
        # We just need a thread-specific identifier for each combined simulation - the admin port will do nicely
        if self.file_paths:
            return _combine_simulations(
                [os.path.join(data_dir, p) for p in self.file_paths], domains_to_block=(), worker=admin_port
            )
        return _combine_simulations(simulations=[BLOCK_DOMAIN_TEMPLATE], domains_to_block=(), worker=admin_port)


class GeneratedSimulation:  # pylint: disable=R0903

    """Data class for static Hoverfly simulation files

    :str file: the file simulations are recorded to or read from
    :int max_age: if not None, tells the tests how long a generated simulation is valid for (in seconds)
    :dict capture_config: overrides the existing Hoverfly simulation capture settings
    :tuple static_files: static file simulations that get used in combination with recorded simulations.
        These aren't used when a simulation is being recorded.
    """

    file_type = "generated"
    default_static_files = []

    def __init__(self, file: str = None, max_age: int = None, capture_config=None, static_files=()):
        self.file = os.path.join(self.file_type, file or f"temp_{time.time()}.json")
        self.max_age = max_age
        self.capture_config = capture_config
        self.static_files = list(static_files) + self.default_static_files
        self.static_files = [os.path.join("static", file) for file in self.static_files]

    def full_file_path(self, data_dir, admin_port):
        for sim in self.static_files:
            logger.info("Static simulations used in test: %s", sim)
        if self.static_files:
            # The order is important here: `extra` typically contains fallback matchers.
            # So add it first so that Hoverfly prioritises matchers in the recorded simulation.
            return _combine_simulations(
                [os.path.join(data_dir, p) for p in (*self.static_files, self.file)], (), admin_port
            )
        return os.path.join(data_dir, self.file)


def _combine_simulations(simulations, domains_to_block, worker):
    with open(simulations[0]) as file:
        combined_sim = json.load(file)

    for sim in simulations[1:]:
        with open(sim) as file:
            pairs = json.load(file)["data"]["pairs"]
            combined_sim["data"]["pairs"] += pairs
    for domain in domains_to_block:
        pairs = template_block_domain_json(domain)["data"]["pairs"]
        combined_sim["data"]["pairs"] += pairs
    file_name = f"combined_temp_{worker}.json"
    with open(file_name, "w") as file:
        file.write(json.dumps(combined_sim, indent=4, separators=(",", ": ")))
    return file_name


def template_block_domain_json(domain):
    with open(BLOCK_DOMAIN_TEMPLATE) as file:
        sim = file.read()
        sim = sim.replace("<DOMAIN>", domain)

    return json.loads(sim)


BLOCK_DOMAIN_TEMPLATE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "block_domain_template.json")

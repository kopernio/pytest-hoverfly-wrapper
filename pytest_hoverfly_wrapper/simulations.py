import os
import time


class StaticSimulation:
    # TODO: consider creating a common Simulation interface in the future, if these classes get big
    file_type = "static"
    max_age = None  # Static simulations have no expiry

    def __init__(self, files: list = None, block_domains: list = ()):
        """
        :list file: list of files that are used in the simulation
        :list block_domains: list of domains (or domain glob patterns) for which simulations will be generated to
        block requests to.
        """
        self.files = files if files else []
        self.block_domains = block_domains

        self.file_paths = [os.path.join(self.file_type, file) for file in self.files]


class GeneratedSimulation:
    file_type = "generated"
    default_static_files = []

    def __init__(self, file: str = None, max_age: int = None, capture_config=None, static_files=()):
        """
        :str file: the file simulations are recorded to or read from
        :int max_age: if not None, tells the tests how long a generated simulation is valid for (in seconds)
        :dict capture_config: overrides the existing Hoverfly simulation capture settings
        :tuple static_files: static file simulations that get used in combination with recorded simulations. These aren't used when a simulation is being recorded.
        """
        self.file = os.path.join(self.file_type, file or "temp_{}.json".format(time.time()))
        self.max_age = max_age
        self.capture_config = capture_config
        self.static_files = list(static_files) + self.default_static_files
        self.static_files = [os.path.join("static", file) for file in self.static_files]

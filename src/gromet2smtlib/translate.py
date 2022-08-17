import json

from automates.program_analysis.JSON2GroMEt.json2gromet import json_to_gromet

# TODO more descriptive name
class QueryableGromet(object):

    def __init__(self, gromet_fn) -> None:
        self._gromet_fn = gromet_fn

    # STUB This is where we will read in an process the gromet file
    def query(this, query_str):
        return True

    # STUB Read the gromet file into some object
    @staticmethod
    def from_gromet_file(gromet_path):
        return QueryableGromet(json_to_gromet(gromet_path))


class QueryableBilayer(QueryableModel):
    def __init__(self):
        pass

    # STUB This is where we will read in and process the bilayer file
    def query(query_str):
        return False

    # STUB Read the bilayer file into some object
    @staticmethod
    def from_bilayer_file(gromet_path):
        return QueryableBilayer(json_to_gromet(gromet_path))

class Bilayer():
    def __init__(self):
        
class Series:
    # Class-level attributes to define column headings and field labels
    headings = ['ID', 'Name', 'DateCreation', 'Season', 'Director', 'PosFile', 'Erased']
    fields = {
        '-ID-': 'Serie ID:',
        '-Name-': 'Serie Name:',
        '-DateCreation-': 'Date of Creation:',
        '-Season-': 'Season:',
        '-Director-': 'Director:',
        '-PosFile-': 'Position into File',
    }

    # Set to keep track of used series IDs
    used_ids = set()

    # Constructor to initialize series instances with specific attributes
    def __init__(self, ID="", name="", datecreation="", season="", director="", posFile="", erased=0):
        # Ensure unique series IDs using the 'used_ids' set
        if ID not in Series.used_ids:
            self.ID = ID
            Series.used_ids.add(ID)
        else:
            raise ValueError(f"The ID {ID} has already been assigned to another series.")

        # Assign other series attributes
        self.name = name
        self.datecreation = datecreation
        self.season = season
        self.director = director
        self.posFile = posFile
        self.erased = erased

    # Method to convert series information into a list representing a row
    def to_row(self):
        return [self.ID, self.name, self.datecreation, self.season, self.director, self.posFile, self.erased]

    # Custom equality method to compare series based on 'posFile'
    def __eq__(self, other_series):
        return other_series.posFile == self.posFile

    # String representation of a series instance
    def __str__(self):
        return f"Series(ID={self.ID}, Name={self.name}, DateCreation={self.datecreation}, Season={self.season}, Director={self.director}, PosFile={self.posFile}, Erased={self.erased})"

    # Method to check if the series is in a specific position
    def series_in_pos(self, pos):
        return self.posFile == pos

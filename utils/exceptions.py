class InvalidConfig(Exception):
    def __init__(self, setting, expected_type, subsetting=None):
        self.setting = setting
        self.subsetting = subsetting
        self.expected_type = expected_type
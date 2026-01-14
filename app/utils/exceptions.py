"""Custom exceptions for the application."""


class IikoAPIError(Exception):
    """Exception raised for iiko API errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(Exception):
    """Exception raised for database errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

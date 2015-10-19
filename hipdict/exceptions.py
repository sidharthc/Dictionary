#Classes to handle different types of exceptions generated


class BaseException(Exception):
    """Generic class for exception handling"""
    value = "Exception"

    def __str__(self):
        return repr(self.value)


class InvalidCredentials(BaseException):
    """This class handles exception when the
    credentials expire or are corrupted"""
    value = "Invalid Credentials!"


class RateLimitExceed(BaseException):
    """This class handles exception when an API is hit too many times"""
    value = "Too many attempts! Try after sometime"


class BadRequest(BaseException):
    """This class handles exception when some parameter of the request is
    either missing or improper."""
    value = "Bad Request!"


class InternalServerError(BaseException):
    """This class handles exception when there is some issue with the code."""
    value = "Internal Server Error!"

class RoadmapError(Exception):
    """Base class for roadmap exceptions"""
    pass


class RoadmapNotFoundError(RoadmapError):
    """Raised when a roadmap is not found"""
    pass


class TopicNotFoundError(RoadmapError):
    """Raised when a topic is not found"""
    pass


class TaskNotFoundError(RoadmapError):
    """Raised when a task is not found"""
    pass


class InvalidRoadmapError(RoadmapError):
    """Raised when Roadmap validation fails"""
    pass


class InvalidTopicError(RoadmapError):
    """Raised when Topic validation fails"""
    pass


class InvalidTaskError(RoadmapError):
    """Raised when Task validation fails"""
    pass


class UserNotFoundError(Exception):
    """Raised when a user is not found"""
    pass


class UserAlreadyExistsError(Exception):
    """Raised when a user already exists"""
    pass


class InvalidRoadmapIdError(Exception):
    """Raised when an invalid roadmap ID is provided"""
    pass

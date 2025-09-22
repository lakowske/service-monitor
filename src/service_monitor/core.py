"""Core functionality for the clean Python project."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
logger = logging.getLogger(__name__)


# Pydantic models for data validation
class UserProfile(BaseModel):
    """User profile with validation using Pydantic."""

    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Valid email address")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age in years")
    tags: list[str] = Field(default_factory=list, description="User tags")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Profile creation time"
    )

    @model_validator(mode="after")
    def validate_model(self) -> "UserProfile":
        """Validate the entire model."""
        # Validate name doesn't contain numbers
        if any(char.isdigit() for char in self.name):
            raise ValueError("Name cannot contain numbers")
        self.name = self.name.strip().title()

        # Validate tags are not empty
        self.tags = [tag.strip().lower() for tag in self.tags if tag.strip()]

        return self

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


# Dataclass for simple data structures
@dataclass
class CalculationResult:
    """Result of a mathematical calculation."""

    operand_a: Union[int, float]
    operand_b: Union[int, float]
    operation: str
    result: Union[int, float]
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate data after initialization."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if not isinstance(self.operand_a, (int, float)):
            raise TypeError("operand_a must be a number")
        if not isinstance(self.operand_b, (int, float)):
            raise TypeError("operand_b must be a number")
        if not isinstance(self.operation, str):
            raise TypeError("operation must be a string")
        if not isinstance(self.result, (int, float)):
            raise TypeError("result must be a number")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "operand_a": self.operand_a,
            "operand_b": self.operand_b,
            "operation": self.operation,
            "result": self.result,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class ApplicationConfig:
    """Application configuration using dataclass."""

    debug: bool = False
    log_level: str = "INFO"
    max_users: int = 1000
    timeout: float = 30.0
    features: Optional[list[str]] = None

    def __post_init__(self) -> None:
        """Initialize features list if None."""
        if self.features is None:
            self.features = ["basic", "logging"]


# Core functionality
def greet(name: str) -> str:
    """Greet a person with their name.

    Args:
        name: The name of the person to greet.

    Returns:
        A greeting message.

    Example:
        >>> greet("World")
        'Hello, World!'
    """
    logger.info(f"Greeting user - name: {name}")

    if not isinstance(name, str):
        logger.error(f"Invalid name type - expected: str, got: {type(name)}")
        raise TypeError("Name must be a string")
    if not name.strip():
        logger.error("Empty name provided")
        raise ValueError("Name cannot be empty")

    greeting = f"Hello, {name.strip()}!"
    logger.debug(f"Generated greeting - message: {greeting}")
    return greeting


def calculate_sum(a: Union[int, float], b: Union[int, float]) -> CalculationResult:
    """Calculate the sum of two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        CalculationResult containing the operation details.

    Example:
        >>> result = calculate_sum(2, 3)
        >>> result.result
        5
        >>> result.operation
        'addition'
    """
    logger.info(f"Calculating sum - operand_a: {a}, operand_b: {b}")

    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        logger.error(f"Invalid operand types - a: {type(a)}, b: {type(b)}")
        raise TypeError("Both arguments must be numbers")

    result = a + b
    calculation_result = CalculationResult(operand_a=a, operand_b=b, operation="addition", result=result)

    logger.debug(f"Sum calculation complete - result: {result}")
    return calculation_result


def create_user_profile(
    name: str, email: str, age: Optional[int] = None, tags: Optional[list[str]] = None
) -> UserProfile:
    """Create a validated user profile.

    Args:
        name: User's full name.
        email: User's email address.
        age: User's age (optional).
        tags: List of tags (optional).

    Returns:
        Validated UserProfile instance.

    Raises:
        ValidationError: If the input data is invalid.

    Example:
        >>> profile = create_user_profile("John Doe", "john@example.com", 30, ["developer", "python"])
        >>> profile.name
        'John Doe'
        >>> profile.email
        'john@example.com'
    """
    logger.info(f"Creating user profile - name: {name}, email: {email}")

    try:
        profile = UserProfile(name=name, email=email, age=age, tags=tags or [])
        logger.debug(f"User profile created successfully - id: {id(profile)}")
        return profile
    except Exception as e:
        logger.error(f"Failed to create user profile - error: {str(e)}")
        raise


def main() -> None:
    """Main entry point for the application."""
    logger.info("Starting application")

    # Configuration example
    config = ApplicationConfig(debug=True, log_level="DEBUG")
    logger.info(f"Application configuration - debug: {config.debug}, features: {config.features}")

    # Basic greeting
    greeting = greet("World")
    print(greeting)

    # Math calculation with dataclass
    calc_result = calculate_sum(2, 3)
    print(f"{calc_result.operand_a} + {calc_result.operand_b} = {calc_result.result}")
    print(f"Calculation performed at: {calc_result.timestamp}")

    # Float calculation
    float_result = calculate_sum(2.5, 1.5)
    print(f"{float_result.operand_a} + {float_result.operand_b} = {float_result.result}")

    # User profile with Pydantic validation
    try:
        profile = create_user_profile(
            name="Jane Doe", email="jane@example.com", age=25, tags=["developer", "python", "clean-code"]
        )
        print(f"Created profile for {profile.name} ({profile.email})")
        print(f"Profile tags: {', '.join(profile.tags)}")
        print(f"Profile created at: {profile.created_at}")
    except Exception as e:
        logger.error(f"Failed to create user profile - error: {str(e)}")
        print(f"Error creating profile: {e}")

    logger.info("Application completed successfully")


if __name__ == "__main__":
    main()

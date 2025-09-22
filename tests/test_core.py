"""Tests for core functionality."""

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from service_monitor.core import (
    ApplicationConfig,
    CalculationResult,
    UserProfile,
    calculate_sum,
    create_user_profile,
    greet,
)


# Tests for greeting functionality
def test_greet_with_valid_name() -> None:
    """Test greeting with a valid name."""
    result = greet("Alice")
    assert result == "Hello, Alice!"


def test_greet_with_name_with_spaces() -> None:
    """Test greeting with name containing spaces."""
    result = greet("  Alice  ")
    assert result == "Hello, Alice!"


def test_greet_with_empty_name() -> None:
    """Test greeting with an empty name raises ValueError."""
    with pytest.raises(ValueError, match="Name cannot be empty"):
        greet("")


def test_greet_with_whitespace_name() -> None:
    """Test greeting with whitespace-only name raises ValueError."""
    with pytest.raises(ValueError, match="Name cannot be empty"):
        greet("   ")


def test_greet_with_non_string() -> None:
    """Test greeting with non-string input raises TypeError."""
    invalid_input: Any = 123
    with pytest.raises(TypeError, match="Name must be a string"):
        greet(invalid_input)


# Tests for calculation functionality
def test_calculate_sum_integers() -> None:
    """Test sum calculation with integers."""
    result = calculate_sum(2, 3)
    assert isinstance(result, CalculationResult)
    assert result.operand_a == 2
    assert result.operand_b == 3
    assert result.operation == "addition"
    assert result.result == 5
    assert isinstance(result.timestamp, datetime)


def test_calculate_sum_floats() -> None:
    """Test sum calculation with floats."""
    result = calculate_sum(2.5, 1.5)
    assert isinstance(result, CalculationResult)
    assert result.operand_a == 2.5
    assert result.operand_b == 1.5
    assert result.result == 4.0


def test_calculate_sum_mixed() -> None:
    """Test sum calculation with mixed int and float."""
    result = calculate_sum(2, 3.5)
    assert isinstance(result, CalculationResult)
    assert result.operand_a == 2
    assert result.operand_b == 3.5
    assert result.result == 5.5


def test_calculate_sum_with_non_numbers() -> None:
    """Test sum calculation with non-numeric input raises TypeError."""
    invalid_first: Any = "2"
    invalid_second: Any = "3"

    with pytest.raises(TypeError, match="Both arguments must be numbers"):
        calculate_sum(invalid_first, 3)

    with pytest.raises(TypeError, match="Both arguments must be numbers"):
        calculate_sum(2, invalid_second)


# Tests for CalculationResult dataclass
def test_calculation_result_creation() -> None:
    """Test CalculationResult creation."""
    result = CalculationResult(operand_a=10, operand_b=5, operation="subtraction", result=5)
    assert result.operand_a == 10
    assert result.operand_b == 5
    assert result.operation == "subtraction"
    assert result.result == 5
    assert isinstance(result.timestamp, datetime)


def test_calculation_result_to_dict() -> None:
    """Test CalculationResult to_dict method."""
    result = CalculationResult(operand_a=10, operand_b=5, operation="subtraction", result=5)
    dict_result = result.to_dict()
    assert dict_result["operand_a"] == 10
    assert dict_result["operand_b"] == 5
    assert dict_result["operation"] == "subtraction"
    assert dict_result["result"] == 5
    assert "timestamp" in dict_result


def test_calculation_result_invalid_operands() -> None:
    """Test CalculationResult with invalid operands."""
    with pytest.raises(TypeError, match="operand_a must be a number"):
        CalculationResult(operand_a="invalid", operand_b=5, operation="test", result=5)

    with pytest.raises(TypeError, match="operand_b must be a number"):
        CalculationResult(operand_a=5, operand_b="invalid", operation="test", result=5)


# Tests for UserProfile Pydantic model
def test_user_profile_creation() -> None:
    """Test UserProfile creation with valid data."""
    profile = UserProfile(name="John Doe", email="john@example.com", age=30, tags=["developer", "python"])
    assert profile.name == "John Doe"
    assert profile.email == "john@example.com"
    assert profile.age == 30
    assert profile.tags == ["developer", "python"]
    assert isinstance(profile.created_at, datetime)


def test_user_profile_name_validation() -> None:
    """Test UserProfile name validation."""
    # Test name with numbers
    with pytest.raises(ValidationError) as exc_info:
        UserProfile(name="John123", email="john@example.com")
    assert "Name cannot contain numbers" in str(exc_info.value)

    # Test name too long
    with pytest.raises(ValidationError):
        UserProfile(name="a" * 101, email="john@example.com")

    # Test empty name
    with pytest.raises(ValidationError):
        UserProfile(name="", email="john@example.com")


def test_user_profile_email_validation() -> None:
    """Test UserProfile email validation."""
    with pytest.raises(ValidationError):
        UserProfile(name="John Doe", email="invalid-email")
    with pytest.raises(ValidationError):
        UserProfile(name="John Doe", email="@example.com")
    with pytest.raises(ValidationError):
        UserProfile(name="John Doe", email="john@")


def test_user_profile_age_validation() -> None:
    """Test UserProfile age validation."""
    # Test negative age
    with pytest.raises(ValidationError):
        UserProfile(name="John Doe", email="john@example.com", age=-1)
    # Test age too high
    with pytest.raises(ValidationError):
        UserProfile(name="John Doe", email="john@example.com", age=121)


def test_user_profile_tags_validation() -> None:
    """Test UserProfile tags validation."""
    profile = UserProfile(
        name="John Doe", email="john@example.com", tags=["  Developer  ", "Python", "  ", "Clean-Code  "]
    )
    assert profile.tags == ["developer", "python", "clean-code"]


def test_user_profile_name_formatting() -> None:
    """Test UserProfile name formatting."""
    profile = UserProfile(name="  john doe  ", email="john@example.com")
    assert profile.name == "John Doe"


def test_create_user_profile_function() -> None:
    """Test create_user_profile function."""
    profile = create_user_profile(name="Jane Smith", email="jane@example.com", age=25, tags=["developer", "python"])
    assert isinstance(profile, UserProfile)
    assert profile.name == "Jane Smith"
    assert profile.email == "jane@example.com"
    assert profile.age == 25
    assert profile.tags == ["developer", "python"]


def test_create_user_profile_with_invalid_data() -> None:
    """Test create_user_profile with invalid data."""
    with pytest.raises(ValidationError):
        create_user_profile(name="John123", email="john@example.com")


# Tests for ApplicationConfig dataclass
def test_application_config_defaults() -> None:
    """Test ApplicationConfig with default values."""
    config = ApplicationConfig()
    assert config.debug is False
    assert config.log_level == "INFO"
    assert config.max_users == 1000
    assert config.timeout == 30.0
    assert config.features == ["basic", "logging"]


def test_application_config_custom_values() -> None:
    """Test ApplicationConfig with custom values."""
    config = ApplicationConfig(
        debug=True, log_level="DEBUG", max_users=500, timeout=60.0, features=["advanced", "monitoring"]
    )
    assert config.debug is True
    assert config.log_level == "DEBUG"
    assert config.max_users == 500
    assert config.timeout == 60.0
    assert config.features == ["advanced", "monitoring"]


def test_application_config_none_features() -> None:
    """Test ApplicationConfig with None features."""
    config = ApplicationConfig(features=None)
    assert config.features == ["basic", "logging"]

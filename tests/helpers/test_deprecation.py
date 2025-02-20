"""Test deprecation helpers."""
import logging
import sys
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.deprecation import (
    DeprecatedConstant,
    DeprecatedConstantEnum,
    check_if_deprecated_constant,
    deprecated_class,
    deprecated_function,
    deprecated_substitute,
    dir_with_deprecated_constants,
    get_deprecated,
)

from tests.common import MockModule, mock_integration


class MockBaseClassDeprecatedProperty:
    """Mock base class for deprecated testing."""

    @property
    @deprecated_substitute("old_property")
    def new_property(self):
        """Test property to fetch."""
        return "default_new"


@patch("logging.getLogger")
def test_deprecated_substitute_old_class(mock_get_logger) -> None:
    """Test deprecated class object."""

    class MockDeprecatedClass(MockBaseClassDeprecatedProperty):
        """Mock deprecated class object."""

        @property
        def old_property(self):
            """Test property to fetch."""
            return "old"

    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    mock_object = MockDeprecatedClass()
    assert mock_object.new_property == "old"
    assert mock_logger.warning.called
    assert len(mock_logger.warning.mock_calls) == 1


@patch("logging.getLogger")
def test_deprecated_substitute_default_class(mock_get_logger) -> None:
    """Test deprecated class object."""

    class MockDefaultClass(MockBaseClassDeprecatedProperty):
        """Mock updated class object."""

    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    mock_object = MockDefaultClass()
    assert mock_object.new_property == "default_new"
    assert not mock_logger.warning.called


@patch("logging.getLogger")
def test_deprecated_substitute_new_class(mock_get_logger) -> None:
    """Test deprecated class object."""

    class MockUpdatedClass(MockBaseClassDeprecatedProperty):
        """Mock updated class object."""

        @property
        def new_property(self):
            """Test property to fetch."""
            return "new"

    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    mock_object = MockUpdatedClass()
    assert mock_object.new_property == "new"
    assert not mock_logger.warning.called


@patch("logging.getLogger")
def test_config_get_deprecated_old(mock_get_logger) -> None:
    """Test deprecated config."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    config = {"old_name": True}
    assert get_deprecated(config, "new_name", "old_name") is True
    assert mock_logger.warning.called
    assert len(mock_logger.warning.mock_calls) == 1


@patch("logging.getLogger")
def test_config_get_deprecated_new(mock_get_logger) -> None:
    """Test deprecated config."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    config = {"new_name": True}
    assert get_deprecated(config, "new_name", "old_name") is True
    assert not mock_logger.warning.called


@deprecated_class("homeassistant.blah.NewClass")
class MockDeprecatedClass:
    """Mock class for deprecated testing."""


@patch("logging.getLogger")
def test_deprecated_class(mock_get_logger) -> None:
    """Test deprecated class."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    MockDeprecatedClass()
    assert mock_logger.warning.called
    assert len(mock_logger.warning.mock_calls) == 1


@pytest.mark.parametrize(
    ("breaks_in_ha_version", "extra_msg"),
    [
        (None, ""),
        ("2099.1", " which will be removed in HA Core 2099.1"),
    ],
)
def test_deprecated_function(
    caplog: pytest.LogCaptureFixture,
    breaks_in_ha_version: str | None,
    extra_msg: str,
) -> None:
    """Test deprecated_function decorator.

    This tests the behavior when the calling integration is not known.
    """

    @deprecated_function("new_function", breaks_in_ha_version=breaks_in_ha_version)
    def mock_deprecated_function():
        pass

    mock_deprecated_function()
    assert (
        f"mock_deprecated_function is a deprecated function{extra_msg}. "
        "Use new_function instead"
    ) in caplog.text


@pytest.mark.parametrize(
    ("breaks_in_ha_version", "extra_msg"),
    [
        (None, ""),
        ("2099.1", " which will be removed in HA Core 2099.1"),
    ],
)
def test_deprecated_function_called_from_built_in_integration(
    caplog: pytest.LogCaptureFixture,
    breaks_in_ha_version: str | None,
    extra_msg: str,
) -> None:
    """Test deprecated_function decorator.

    This tests the behavior when the calling integration is built-in.
    """

    @deprecated_function("new_function", breaks_in_ha_version=breaks_in_ha_version)
    def mock_deprecated_function():
        pass

    with patch(
        "homeassistant.helpers.frame.extract_stack",
        return_value=[
            Mock(
                filename="/home/paulus/homeassistant/core.py",
                lineno="23",
                line="do_something()",
            ),
            Mock(
                filename="/home/paulus/homeassistant/components/hue/light.py",
                lineno="23",
                line="await session.close()",
            ),
            Mock(
                filename="/home/paulus/aiohue/lights.py",
                lineno="2",
                line="something()",
            ),
        ],
    ):
        mock_deprecated_function()
    assert (
        "mock_deprecated_function was called from hue, "
        f"this is a deprecated function{extra_msg}. "
        "Use new_function instead"
    ) in caplog.text


@pytest.mark.parametrize(
    ("breaks_in_ha_version", "extra_msg"),
    [
        (None, ""),
        ("2099.1", " which will be removed in HA Core 2099.1"),
    ],
)
def test_deprecated_function_called_from_custom_integration(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    breaks_in_ha_version: str | None,
    extra_msg: str,
) -> None:
    """Test deprecated_function decorator.

    This tests the behavior when the calling integration is custom.
    """

    mock_integration(hass, MockModule("hue"), built_in=False)

    @deprecated_function("new_function", breaks_in_ha_version=breaks_in_ha_version)
    def mock_deprecated_function():
        pass

    with patch(
        "homeassistant.helpers.frame.extract_stack",
        return_value=[
            Mock(
                filename="/home/paulus/homeassistant/core.py",
                lineno="23",
                line="do_something()",
            ),
            Mock(
                filename="/home/paulus/config/custom_components/hue/light.py",
                lineno="23",
                line="await session.close()",
            ),
            Mock(
                filename="/home/paulus/aiohue/lights.py",
                lineno="2",
                line="something()",
            ),
        ],
    ):
        mock_deprecated_function()
    assert (
        "mock_deprecated_function was called from hue, "
        f"this is a deprecated function{extra_msg}. "
        "Use new_function instead, please report it to the author of the "
        "'hue' custom integration"
    ) in caplog.text


@pytest.mark.parametrize(
    ("deprecated_constant", "extra_msg"),
    [
        (
            DeprecatedConstant("value", "NEW_CONSTANT", None),
            ". Use NEW_CONSTANT instead",
        ),
        (
            DeprecatedConstant(1, "NEW_CONSTANT", "2099.1"),
            " which will be removed in HA Core 2099.1. Use NEW_CONSTANT instead",
        ),
    ],
)
@pytest.mark.parametrize(
    ("module_name", "extra_extra_msg"),
    [
        ("homeassistant.components.hue.light", ""),  # builtin integration
        (
            "config.custom_components.hue.light",
            ", please report it to the author of the 'hue' custom integration",
        ),  # custom component integration
    ],
)
def test_check_if_deprecated_constant(
    caplog: pytest.LogCaptureFixture,
    deprecated_constant: DeprecatedConstant | DeprecatedConstantEnum,
    extra_msg: str,
    module_name: str,
    extra_extra_msg: str,
) -> None:
    """Test check_if_deprecated_constant."""
    module_globals = {
        "__name__": module_name,
        "_DEPRECATED_TEST_CONSTANT": deprecated_constant,
    }
    filename = f"/home/paulus/{module_name.replace('.', '/')}.py"

    # mock module for homeassistant/helpers/frame.py#get_integration_frame
    sys.modules[module_name] = Mock(__file__=filename)

    with patch(
        "homeassistant.helpers.frame.extract_stack",
        return_value=[
            Mock(
                filename="/home/paulus/homeassistant/core.py",
                lineno="23",
                line="do_something()",
            ),
            Mock(
                filename=filename,
                lineno="23",
                line="await session.close()",
            ),
            Mock(
                filename="/home/paulus/aiohue/lights.py",
                lineno="2",
                line="something()",
            ),
        ],
    ):
        value = check_if_deprecated_constant("TEST_CONSTANT", module_globals)
        assert value == deprecated_constant.value

    assert (
        module_name,
        logging.WARNING,
        f"TEST_CONSTANT was used from hue, this is a deprecated constant{extra_msg}{extra_extra_msg}",
    ) in caplog.record_tuples


def test_test_check_if_deprecated_constant_invalid(
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test check_if_deprecated_constant will raise an attribute error and create an log entry on an invalid deprecation type."""
    module_name = "homeassistant.components.hue.light"
    module_globals = {"__name__": module_name, "_DEPRECATED_TEST_CONSTANT": 1}
    name = "TEST_CONSTANT"

    excepted_msg = (
        f"Value of _DEPRECATED_{name!r} is an instance of <class 'int'> "
        "but an instance of DeprecatedConstant or DeprecatedConstantEnum is required"
    )

    with pytest.raises(AttributeError, match=excepted_msg):
        check_if_deprecated_constant(name, module_globals)

    assert (module_name, logging.DEBUG, excepted_msg) in caplog.record_tuples


@pytest.mark.parametrize(
    ("module_global", "expected"),
    [
        ({"CONSTANT": 1}, ["CONSTANT"]),
        ({"_DEPRECATED_CONSTANT": 1}, ["_DEPRECATED_CONSTANT", "CONSTANT"]),
        (
            {"_DEPRECATED_CONSTANT": 1, "SOMETHING": 2},
            ["_DEPRECATED_CONSTANT", "SOMETHING", "CONSTANT"],
        ),
    ],
)
def test_dir_with_deprecated_constants(
    module_global: dict[str, Any], expected: list[str]
) -> None:
    """Test dir() with deprecated constants."""
    assert dir_with_deprecated_constants(module_global) == expected

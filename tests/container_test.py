#!/usr/bin/env pytest -vs
"""Tests for Docker container."""

# Standard Python Libraries
import time


def test_container_running(main_container):
    """Test that the container has started."""
    # Wait until the container is running or timeout.
    for _ in range(10):
        main_container.reload()
        if main_container.status != "created":
            break
        time.sleep(1)
    assert main_container.status in ("exited", "running")


def test_wait_for_container_exit(main_container):
    """Wait for version container to exit cleanly."""
    assert (
        main_container.wait()["StatusCode"] == 0
    ), "The container did not exit cleanly"

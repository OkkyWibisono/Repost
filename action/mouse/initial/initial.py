"""
Human-like mouse initialization and movement.
Uses natural curves, jitter, and ease-in-out timing.
"""

import pyautogui
import random
import math
import time
from typing import Tuple

# Disable pyautogui fail-safe for smoother operation (move mouse to corner to abort)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out: slow start, fast middle, slow end."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def ease_in_out_quint(t: float) -> float:
    """Quintic ease-in-out: even smoother slow-fast-slow."""
    if t < 0.5:
        return 16 * t * t * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 5) / 2


def add_jitter(value: float, intensity: float = 1.0) -> float:
    """Add random jitter to a value."""
    return value + random.gauss(0, intensity)


def get_random_screen_position(margin: int = 50) -> Tuple[int, int]:
    """Get a random position on screen with margin from edges."""
    screen_width, screen_height = pyautogui.size()
    x = random.randint(margin, screen_width - margin)
    y = random.randint(margin, screen_height - margin)
    return x, y


def bezier_point(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Calculate a point on a cubic Bezier curve."""
    return (
        pow(1 - t, 3) * p0 +
        3 * pow(1 - t, 2) * t * p1 +
        3 * (1 - t) * pow(t, 2) * p2 +
        pow(t, 3) * p3
    )


def generate_control_points(
    start: Tuple[int, int],
    end: Tuple[int, int],
    curvature: float = 0.3
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Generate random control points for Bezier curve."""
    sx, sy = start
    ex, ey = end

    # Distance between points
    dist = math.sqrt((ex - sx) ** 2 + (ey - sy) ** 2)

    # Random perpendicular offset for control points
    angle = math.atan2(ey - sy, ex - sx)
    perp_angle = angle + math.pi / 2

    # Control point 1 (closer to start)
    offset1 = random.uniform(-dist * curvature, dist * curvature)
    cp1_x = sx + (ex - sx) * 0.25 + math.cos(perp_angle) * offset1
    cp1_y = sy + (ey - sy) * 0.25 + math.sin(perp_angle) * offset1

    # Control point 2 (closer to end)
    offset2 = random.uniform(-dist * curvature, dist * curvature)
    cp2_x = sx + (ex - sx) * 0.75 + math.cos(perp_angle) * offset2
    cp2_y = sy + (ey - sy) * 0.75 + math.sin(perp_angle) * offset2

    return (cp1_x, cp1_y), (cp2_x, cp2_y)


def human_move(
    target_x: int,
    target_y: int,
    duration: float = None,
    jitter_intensity: float = 2.0,
    steps_per_second: int = 120
) -> None:
    """
    Move mouse to target with human-like motion.

    Args:
        target_x: Target X coordinate
        target_y: Target Y coordinate
        duration: Movement duration (randomized if None)
        jitter_intensity: Amount of random jitter (pixels)
        steps_per_second: Movement smoothness
    """
    start_x, start_y = pyautogui.position()

    # Calculate distance for duration estimation
    distance = math.sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)

    # Randomize duration based on distance if not specified
    if duration is None:
        # Base duration + distance factor + random variation
        base_duration = random.uniform(0.3, 0.6)
        distance_factor = distance / 2000  # Longer distance = more time
        random_factor = random.uniform(0.9, 1.3)
        duration = (base_duration + distance_factor) * random_factor
        duration = max(0.2, min(duration, 2.0))  # Clamp between 0.2 and 2.0 seconds

    # Generate Bezier control points for curved path
    cp1, cp2 = generate_control_points((start_x, start_y), (target_x, target_y))

    # Calculate number of steps
    num_steps = max(int(duration * steps_per_second), 10)

    # Generate path points
    for i in range(num_steps + 1):
        # Progress through the curve (0 to 1)
        t = i / num_steps

        # Apply ease-in-out to timing
        eased_t = ease_in_out_cubic(t)

        # Calculate position on Bezier curve
        x = bezier_point(eased_t, start_x, cp1[0], cp2[0], target_x)
        y = bezier_point(eased_t, start_y, cp1[1], cp2[1], target_y)

        # Add jitter (less at start and end, more in middle)
        jitter_factor = math.sin(t * math.pi)  # 0 at edges, 1 in middle
        current_jitter = jitter_intensity * jitter_factor

        if current_jitter > 0 and i < num_steps:  # No jitter on final position
            x = add_jitter(x, current_jitter)
            y = add_jitter(y, current_jitter)

        # Move mouse
        pyautogui.moveTo(int(x), int(y), _pause=False)

        # Variable delay between steps (slight randomization)
        step_delay = (duration / num_steps) * random.uniform(0.8, 1.2)
        time.sleep(step_delay)

    # Final precise move to target (remove any jitter error)
    pyautogui.moveTo(target_x, target_y, _pause=False)


def human_move_with_overshoot(
    target_x: int,
    target_y: int,
    overshoot_chance: float = 0.3
) -> None:
    """
    Move to target with occasional overshoot and correction.

    Args:
        target_x: Target X coordinate
        target_y: Target Y coordinate
        overshoot_chance: Probability of overshooting (0-1)
    """
    if random.random() < overshoot_chance:
        # Calculate overshoot position
        start_x, start_y = pyautogui.position()
        direction_x = target_x - start_x
        direction_y = target_y - start_y

        overshoot_factor = random.uniform(1.05, 1.15)
        overshoot_x = int(start_x + direction_x * overshoot_factor)
        overshoot_y = int(start_y + direction_y * overshoot_factor)

        # Move to overshoot position
        human_move(overshoot_x, overshoot_y)

        # Brief pause (human reaction time)
        time.sleep(random.uniform(0.05, 0.15))

        # Correct to actual target
        human_move(target_x, target_y, duration=random.uniform(0.1, 0.25))
    else:
        human_move(target_x, target_y)


def random_idle_movement(duration: float = 1.5, movements: int = None) -> None:
    """
    Perform random idle mouse movements.

    Args:
        duration: Total duration of idle movement
        movements: Number of small movements (randomized if None)
    """
    if movements is None:
        movements = random.randint(2, 5)

    time_per_movement = duration / movements

    for i in range(movements):
        current_x, current_y = pyautogui.position()

        # Small random offset (idle fidgeting)
        offset_x = random.randint(-30, 30)
        offset_y = random.randint(-20, 20)

        new_x = max(10, min(current_x + offset_x, pyautogui.size()[0] - 10))
        new_y = max(10, min(current_y + offset_y, pyautogui.size()[1] - 10))

        human_move(new_x, new_y, duration=time_per_movement * random.uniform(0.3, 0.6))

        # Random micro-pause
        time.sleep(random.uniform(0.1, time_per_movement * 0.5))


def initialize() -> None:
    """
    Initialize mouse at random position with human-like movement.
    Called when page is loaded.
    """
    print("Initializing mouse movement...")

    # Get current and random target positions
    screen_width, screen_height = pyautogui.size()
    print(f"Screen size: {screen_width}x{screen_height}")

    # Start position (current or random)
    start_x, start_y = pyautogui.position()
    print(f"Current position: ({start_x}, {start_y})")

    # Move to random initial position
    random_x, random_y = get_random_screen_position(margin=100)
    print(f"Moving to random position: ({random_x}, {random_y})")

    human_move(random_x, random_y)

    # Wait with slight idle movement
    print("Waiting 1.5 seconds with idle movement...")
    random_idle_movement(duration=1.5)

    # Move to another random position
    target_x, target_y = get_random_screen_position(margin=100)
    print(f"Moving to target position: ({target_x}, {target_y})")

    human_move_with_overshoot(target_x, target_y, overshoot_chance=0.25)

    print("Mouse initialization complete.")


if __name__ == "__main__":
    # Test the mouse initialization
    print("Starting mouse initialization test...")
    time.sleep(1)  # Give time to switch windows if needed
    initialize()

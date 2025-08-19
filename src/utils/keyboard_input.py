"""
Cross-platform keyboard input utilities with ESC key detection support.

This module provides functions to capture keyboard input with special key detection,
particularly the ESC key, across Windows, macOS, and Linux systems.
"""

import sys
import os
from typing import Optional

from src.utils.logger import logger


# Special return value for ESC key press
ESC_PRESSED = "__ESC_PRESSED__"


def get_key_input(prompt: str) -> str:
    """Get user input with ESC detection support across platforms.
    
    Args:
        prompt: The prompt to display to the user
        
    Returns:
        User input string, or ESC_PRESSED constant if ESC key was pressed
    """
    print(f"{prompt} (ESC para voltar)")
    
    try:
        if sys.platform != 'win32':
            # Unix/Linux/macOS implementation
            logger.debug("Using Unix terminal input method")
            return _get_key_unix()
        else:
            # Windows implementation
            logger.debug("Using Windows terminal input method")
            return _get_key_windows()
    except (ImportError, ModuleNotFoundError, AttributeError, OSError) as e:
        # Fallback to regular input if special key detection fails
        logger.info(f"Special key detection failed, using standard input: {e}")
        return _get_key_fallback()


def _get_key_unix() -> str:
    """Unix/Linux/macOS key detection using termios."""
    try:
        # Import Unix-specific modules only when needed
        import termios
        import tty
        import select
        
        # Check if stdin is a TTY (not redirected)
        if not sys.stdin.isatty():
            logger.debug("stdin is not a TTY, using fallback input")
            return _get_key_fallback()
        
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            
            # Read input character by character
            chars = []
            while True:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    
                    # ESC key (ASCII 27)
                    if ord(char) == 27:
                        # Check if it's a real ESC or part of escape sequence
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            # It's an escape sequence, consume it
                            next_char = sys.stdin.read(1)
                            if next_char == '[':
                                # Arrow keys, function keys, etc.
                                sys.stdin.read(1)  # consume the rest
                                continue
                        else:
                            # Real ESC key
                            return ESC_PRESSED
                    
                    # Enter key
                    elif ord(char) in [10, 13]:  # \n or \r
                        break
                    
                    # Backspace
                    elif ord(char) == 127:
                        if chars:
                            chars.pop()
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                    
                    # Regular character
                    elif ord(char) >= 32:  # Printable characters
                        chars.append(char)
                        sys.stdout.write(char)
                        sys.stdout.flush()
            
            print()  # New line after input
            return ''.join(chars).strip()
            
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    except (ImportError, ModuleNotFoundError, OSError) as e:
        logger.debug(f"Unix terminal modules not available or operation not supported: {e}")
        # Fallback to regular input
        return _get_key_fallback()


def _get_key_windows() -> str:
    """Windows key detection using msvcrt."""
    try:
        import msvcrt
        logger.debug("Using msvcrt for Windows key detection")
        chars = []
        
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                
                # ESC key
                if ord(char) == 27:
                    return ESC_PRESSED
                
                # Enter key
                elif ord(char) in [10, 13]:
                    break
                
                # Backspace
                elif ord(char) == 8:
                    if chars:
                        chars.pop()
                        msvcrt.putch(b'\b')
                        msvcrt.putch(b' ')
                        msvcrt.putch(b'\b')
                
                # Regular character
                elif ord(char) >= 32:
                    try:
                        chars.append(char.decode('utf-8'))
                        msvcrt.putch(char)
                    except UnicodeDecodeError:
                        # Handle non-UTF-8 characters gracefully
                        continue
        
        print()  # New line after input
        return ''.join(chars).strip()
        
    except (ImportError, ModuleNotFoundError) as e:
        logger.debug(f"Windows terminal modules not available: {e}")
        # Fallback to regular input
        return _get_key_fallback()


def _get_key_fallback() -> str:
    """Fallback method using standard input with ESC simulation."""
    print("(Digite 'esc' para voltar)")
    user_input = input().strip().lower()
    if user_input == 'esc':
        return ESC_PRESSED
    return user_input


def is_esc_pressed(user_input: str) -> bool:
    """Check if the input represents an ESC key press.
    
    Args:
        user_input: The input string to check
        
    Returns:
        True if input represents ESC key press, False otherwise
    """
    return user_input == ESC_PRESSED


def get_simple_input(prompt: str) -> Optional[str]:
    """Get user input with ESC support, returning None if ESC was pressed.
    
    This is a convenience function for simple yes/no scenarios.
    
    Args:
        prompt: The prompt to display to the user
        
    Returns:
        User input string, or None if ESC key was pressed
    """
    result = get_key_input(prompt)
    if is_esc_pressed(result):
        return None
    return result
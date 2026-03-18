"""
Speech-to-Text Module

This module provides functionality to convert spoken audio to text
using the speech_recognition library with Google's Speech Recognition API.
"""

import speech_recognition as sr


def listen_for_speech(timeout: int = 5, phrase_time_limit: int = 10) -> str:
    """
    Listen to microphone input and convert speech to text.

    Args:
        timeout: Maximum time to wait for speech to start (in seconds).
        phrase_time_limit: Maximum time for a single phrase (in seconds).

    Returns:
        The recognized text from speech, or empty string if not understood.

    Example:
        >>> text = listen_for_speech()
        >>> print(f"You said: {text}")
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as microphone:
        # Adjust for ambient noise to improve recognition accuracy
        recognizer.adjust_for_ambient_noise(microphone, duration=0.5)

        print("Listening... Speak now.")

        try:
            # Listen for audio input
            audio = recognizer.listen(
                microphone,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )
            print("Processing speech...")

            # Convert speech to text using Google's Speech Recognition
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")

            return text

        except sr.WaitTimeoutError:
            print("No speech detected within the timeout period.")
            return ""

        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return ""

        except sr.RequestError as error:
            print(f"Error connecting to speech recognition service: {error}")
            return ""


def get_speech_input() -> str:
    """
    Convenience function to get speech input from the user.

    This is a wrapper around listen_for_speech with default settings.

    Returns:
        The recognized text from speech.

    Example:
        >>> user_input = get_speech_input()
        >>> print(f"User said: {user_input}")
    """
    return listen_for_speech()


__all__ = ["listen_for_speech", "get_speech_input"]
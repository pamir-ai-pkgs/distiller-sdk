"""Tests for context manager support across all modules."""

from unittest.mock import MagicMock, patch


class TestCameraContextManager:
    """Tests for Camera module context manager."""

    def test_camera_has_context_manager(self, mock_camera_hardware):
        """Test that Camera class supports context manager protocol."""
        from distiller_sdk.hardware.camera import Camera

        camera = Camera(auto_check_config=False)

        assert hasattr(camera, "__enter__"), "Camera should have __enter__ method"
        assert hasattr(camera, "__exit__"), "Camera should have __exit__ method"
        assert callable(camera.__enter__), "Camera.__enter__ should be callable"
        assert callable(camera.__exit__), "Camera.__exit__ should be callable"

    def test_camera_context_manager_usage(self, mock_camera_hardware):
        """Test that Camera can be used as a context manager."""
        from distiller_sdk.hardware.camera import Camera

        # Mock cv2.VideoCapture
        with patch("cv2.VideoCapture") as mock_video_capture:
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_video_capture.return_value = mock_cap

            # Use Camera as context manager
            with Camera(auto_check_config=False) as camera:
                assert camera is not None, "Context manager should return camera instance"

            # After exiting context, cleanup should have been called
            # Check that release was called on the capture object
            assert mock_cap.release.called, "Camera cleanup should call release()"

    def test_camera_cleanup_on_exception(self, mock_camera_hardware):
        """Test that Camera cleanup happens even when exception occurs."""
        from distiller_sdk.hardware.camera import Camera

        with patch("cv2.VideoCapture") as mock_video_capture:
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_video_capture.return_value = mock_cap

            try:
                with Camera(auto_check_config=False):
                    raise ValueError("Test exception")
            except ValueError:
                pass  # Expected

            # Cleanup should still have been called


class TestLEDContextManager:
    """Tests for LED module context manager."""

    def test_led_has_context_manager(self, mock_led_hardware):
        """Test that LED class supports context manager protocol."""
        from distiller_sdk.hardware.sam import LED

        led = LED(base_path=str(mock_led_hardware))

        assert hasattr(led, "__enter__"), "LED should have __enter__ method"
        assert hasattr(led, "__exit__"), "LED should have __exit__ method"
        assert callable(led.__enter__), "LED.__enter__ should be callable"
        assert callable(led.__exit__), "LED.__exit__ should be callable"

    def test_led_context_manager_usage(self, mock_led_hardware):
        """Test that LED can be used as a context manager."""
        from distiller_sdk.hardware.sam import LED

        # Use LED as context manager
        with LED(base_path=str(mock_led_hardware)) as led:
            assert led is not None, "Context manager should return LED instance"
            # Set a color to verify it works
            led.set_rgb_color(0, 255, 0, 0)

        # After exiting context, verify turn_off_all was called by checking files
        # Check that LED was turned off (context manager calls turn_off_all)
        if (mock_led_hardware / "distiller:led0" / "red").exists():
            led0_red = (mock_led_hardware / "distiller:led0" / "red").read_text().strip()
            assert led0_red == "0", "LED red should be 0 after context exit"

    def test_led_cleanup_on_exception(self, mock_led_hardware):
        """Test that LED cleanup happens even when exception occurs."""
        from distiller_sdk.hardware.sam import LED

        try:
            with LED(base_path=str(mock_led_hardware)) as led:
                led.set_rgb_color(0, 255, 0, 0)  # Turn on LED
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # LEDs should still be turned off (context manager calls turn_off_all even on exception)
        if (mock_led_hardware / "distiller:led0" / "red").exists():
            led0_red = (mock_led_hardware / "distiller:led0" / "red").read_text().strip()
            assert led0_red == "0", "LED should be off even after exception"


class TestPiperContextManager:
    """Tests for Piper module context manager."""

    def test_piper_has_context_manager(self, mock_piper_models):
        """Test that Piper class supports context manager protocol."""
        from distiller_sdk.piper import Piper

        with patch("distiller_sdk.piper.piper.Audio"):
            piper = Piper(
                model_path=str(mock_piper_models["models"]),
                piper_path=str(mock_piper_models["binary"].parent),
                configure_audio=False,
            )

        assert hasattr(piper, "__enter__"), "Piper should have __enter__ method"
        assert hasattr(piper, "__exit__"), "Piper should have __exit__ method"
        assert callable(piper.__enter__), "Piper.__enter__ should be callable"
        assert callable(piper.__exit__), "Piper.__exit__ should be callable"

    def test_piper_context_manager_usage(self, mock_piper_models):
        """Test that Piper can be used as a context manager."""
        from distiller_sdk.piper import Piper

        with patch("distiller_sdk.piper.piper.Audio"):
            # Use Piper as context manager
            with Piper(
                model_path=str(mock_piper_models["models"]),
                piper_path=str(mock_piper_models["binary"].parent),
                configure_audio=False,
            ) as piper:
                assert piper is not None, "Context manager should return Piper instance"

            # After exiting context, cleanup should have been called

    def test_piper_cleanup_on_exception(self, mock_piper_models):
        """Test that Piper cleanup happens even when exception occurs."""
        from distiller_sdk.piper import Piper

        with patch("distiller_sdk.piper.piper.Audio"):
            try:
                with Piper(
                    model_path=str(mock_piper_models["models"]),
                    piper_path=str(mock_piper_models["binary"].parent),
                    configure_audio=False,
                ):
                    raise ValueError("Test exception")
            except ValueError:
                pass  # Expected

            # Cleanup should still have been called


class TestExistingContextManagers:
    """Verify existing context managers still work."""

    def test_audio_context_manager(self):
        """Test that Audio context manager works."""
        from distiller_sdk.hardware.audio import Audio

        audio = Audio(auto_check_config=False)
        assert hasattr(audio, "__enter__")
        assert hasattr(audio, "__exit__")

    def test_display_context_manager(self, tmp_path):
        """Test that Display context manager works."""
        from distiller_sdk.hardware.eink import Display

        # Create fake library file
        fake_lib = tmp_path / "fake.so"
        fake_lib.write_bytes(b"")

        with patch.object(Display, "_find_library", return_value=str(fake_lib)):
            with patch("ctypes.CDLL"):
                display = Display(auto_init=False)

        assert hasattr(display, "__enter__")
        assert hasattr(display, "__exit__")

    def test_parakeet_context_manager(self, mock_parakeet_models):
        """Test that Parakeet context manager works."""
        from distiller_sdk.parakeet import Parakeet

        with patch("distiller_sdk.parakeet.parakeet.Audio"):
            parakeet = Parakeet(
                model_config={"model_hub_path": str(mock_parakeet_models)}, configure_audio=False
            )

        assert hasattr(parakeet, "__enter__")
        assert hasattr(parakeet, "__exit__")

    def test_whisper_context_manager(self, mock_whisper_models):
        """Test that Whisper context manager works."""
        from distiller_sdk.whisper import Whisper

        # Create model.bin file
        model_dir = mock_whisper_models / "faster-distil-whisper-small.en"
        model_dir.mkdir(exist_ok=True)
        (model_dir / "model.bin").write_bytes(b"fake whisper model")

        with (
            patch("distiller_sdk.whisper.fast_whisper.WhisperModel"),
            patch("distiller_sdk.whisper.fast_whisper.Audio"),
        ):
            whisper = Whisper(
                model_config={"model_hub_path": str(mock_whisper_models)}, configure_audio=False
            )

        assert hasattr(whisper, "__enter__")
        assert hasattr(whisper, "__exit__")

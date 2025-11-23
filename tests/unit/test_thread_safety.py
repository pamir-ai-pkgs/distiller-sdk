"""Tests for thread safety across all hardware and AI modules."""

import threading
import time
from unittest.mock import MagicMock, patch


class TestDisplayThreadSafety:
    """Tests for Display module thread safety."""

    def test_display_has_lock(self, tmp_path):
        """Test that Display class has a thread safety lock."""
        from distiller_sdk.hardware.eink import Display

        # Create fake library file
        fake_lib = tmp_path / "fake.so"
        fake_lib.write_bytes(b"")  # Create empty file

        # Mock library loading
        with patch.object(Display, "_find_library", return_value=str(fake_lib)):
            with patch("ctypes.CDLL"):
                display = Display(auto_init=False)

        assert hasattr(display, "_lock"), "Display should have a _lock attribute"
        assert isinstance(display._lock, type(threading.Lock())), (
            "Display._lock should be a threading.Lock"
        )

    def test_display_concurrent_operations(self, tmp_path, monkeypatch):
        """Test that concurrent display operations are serialized."""
        from distiller_sdk.hardware.eink import Display

        # Create fake library file
        fake_lib = tmp_path / "fake.so"
        fake_lib.write_bytes(b"")

        # Track operation order
        operations = []

        # Mock the library to track operations
        mock_lib = MagicMock()
        mock_lib.display_init.return_value = True
        mock_lib.display_image_auto.return_value = True
        mock_lib.display_get_dimensions = lambda w, h: None

        def mock_display_image(*args, **kwargs):
            operations.append(("display", time.time()))
            time.sleep(0.01)  # Simulate slow operation
            return True

        mock_lib.display_image_auto.side_effect = mock_display_image

        with patch.object(Display, "_find_library", return_value=str(fake_lib)):
            with patch("ctypes.CDLL", return_value=mock_lib):
                display = Display(auto_init=False)
                display._initialized = True

                # Run multiple display operations concurrently
                def display_task(task_id):
                    # Create a fake image file
                    img_file = tmp_path / f"test{task_id}.png"
                    img_file.write_text("fake")
                    try:
                        display.display_image_auto(str(img_file))
                    except Exception:
                        pass  # Ignore errors, we're testing concurrency

                threads = [threading.Thread(target=display_task, args=(i,)) for i in range(3)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

        # With proper locking, operations should be serialized
        # All operations should complete
        assert len(operations) >= 3, "All display operations should complete"


class TestLEDThreadSafety:
    """Tests for LED module thread safety."""

    def test_led_has_lock(self, mock_led_hardware):
        """Test that LED class has a thread safety lock."""
        from distiller_sdk.hardware.sam import LED

        led = LED(base_path=str(mock_led_hardware))

        assert hasattr(led, "_lock"), "LED should have a _lock attribute"
        assert isinstance(led._lock, type(threading.Lock())), "LED._lock should be a threading.Lock"

    def test_led_concurrent_color_changes(self, mock_led_hardware):
        """Test that concurrent LED color changes are serialized."""
        from distiller_sdk.hardware.sam import LED

        led = LED(base_path=str(mock_led_hardware))

        # Track color changes
        color_changes = []

        def set_color_task(led_id, r, g, b):
            try:
                led.set_rgb_color(led_id, r, g, b)
                color_changes.append((led_id, r, g, b, time.time()))
            except Exception:
                pass  # Ignore errors

        # Run multiple color changes concurrently
        threads = [
            threading.Thread(target=set_color_task, args=(0, i * 50, 0, 0)) for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All operations should complete
        assert len(color_changes) >= 5, "All color change operations should complete"

    def test_led_concurrent_animation_changes(self, mock_led_hardware):
        """Test that concurrent LED animation changes are serialized."""
        from distiller_sdk.hardware.sam import LED

        led = LED(base_path=str(mock_led_hardware))

        animation_changes = []

        def set_animation_task(led_id, mode, timing):
            try:
                led.set_animation_mode(led_id, mode, timing)
                animation_changes.append((led_id, mode, timing, time.time()))
            except Exception:
                pass

        # Run multiple animation changes concurrently
        threads = [
            threading.Thread(target=set_animation_task, args=(0, "blink", 500)),
            threading.Thread(target=set_animation_task, args=(0, "fade", 1000)),
            threading.Thread(target=set_animation_task, args=(0, "rainbow", 500)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All operations should complete
        assert len(animation_changes) >= 3, "All animation change operations should complete"


class TestParakeetThreadSafety:
    """Tests for Parakeet module thread safety."""

    def test_parakeet_has_lock(self, mock_parakeet_models, monkeypatch):
        """Test that Parakeet class has a thread safety lock."""
        from distiller_sdk.parakeet import Parakeet

        # Mock Audio to avoid hardware dependency
        with patch("distiller_sdk.parakeet.parakeet.Audio"):
            parakeet = Parakeet(
                model_config={"model_hub_path": str(mock_parakeet_models)}, configure_audio=False
            )

        assert hasattr(parakeet, "_lock"), "Parakeet should have a _lock attribute"
        assert isinstance(parakeet._lock, type(threading.Lock())), (
            "Parakeet._lock should be a threading.Lock"
        )

    def test_parakeet_concurrent_recording_state(self, mock_parakeet_models):
        """Test that Parakeet recording state changes are thread-safe."""
        from distiller_sdk.parakeet import Parakeet

        with patch("distiller_sdk.parakeet.parakeet.Audio"):
            parakeet = Parakeet(
                model_config={"model_hub_path": str(mock_parakeet_models)}, configure_audio=False
            )

        # Mock pyaudio with proper configuration
        mock_pyaudio_class = MagicMock()
        mock_pyaudio_instance = MagicMock()
        mock_pyaudio_class.return_value = mock_pyaudio_instance
        mock_pyaudio_instance.get_device_count.return_value = 1
        # Provide complete device info structure
        mock_pyaudio_instance.get_device_info_by_index.return_value = {
            "name": "test_device",
            "maxInputChannels": 2,
            "maxOutputChannels": 2,
            "defaultSampleRate": 48000.0,
        }
        mock_pyaudio_instance.get_default_input_device_info.return_value = {
            "name": "default_device",
            "maxInputChannels": 2,
        }
        mock_pyaudio_instance.open.return_value = MagicMock()

        with patch("pyaudio.PyAudio", mock_pyaudio_class):
            # Test that concurrent start_recording calls are safe
            results = []

            def start_task():
                result = parakeet.start_recording()
                results.append(result)

            threads = [threading.Thread(target=start_task) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Only one thread should successfully start recording
            # Others should return False (already recording)
            successful = sum(1 for r in results if r)
            assert successful == 1, "Only one thread should successfully start recording"


class TestWhisperThreadSafety:
    """Tests for Whisper module thread safety."""

    def test_whisper_has_lock(self, mock_whisper_models):
        """Test that Whisper class has a thread safety lock."""
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

        assert hasattr(whisper, "_lock"), "Whisper should have a _lock attribute"
        assert isinstance(whisper._lock, type(threading.Lock())), (
            "Whisper._lock should be a threading.Lock"
        )

    def test_whisper_concurrent_recording_state(self, mock_whisper_models):
        """Test that Whisper recording state changes are thread-safe."""
        from distiller_sdk.whisper import Whisper

        # Create model.bin file
        model_dir = mock_whisper_models / "faster-distil-whisper-small.en"
        model_dir.mkdir(exist_ok=True)
        (model_dir / "model.bin").write_bytes(b"fake whisper model")

        # Mock faster_whisper model loading
        with (
            patch("distiller_sdk.whisper.fast_whisper.WhisperModel"),
            patch("distiller_sdk.whisper.fast_whisper.Audio"),
        ):
            whisper = Whisper(
                model_config={"model_hub_path": str(mock_whisper_models)}, configure_audio=False
            )

        # Mock pyaudio with proper configuration
        mock_pyaudio_class = MagicMock()
        mock_pyaudio_instance = MagicMock()
        mock_pyaudio_class.return_value = mock_pyaudio_instance
        mock_pyaudio_instance.get_device_count.return_value = 1
        # Provide complete device info structure
        mock_pyaudio_instance.get_device_info_by_index.return_value = {
            "name": "test_device",
            "maxInputChannels": 2,
            "maxOutputChannels": 2,
            "defaultSampleRate": 48000.0,
        }
        mock_pyaudio_instance.open.return_value = MagicMock()

        with patch("pyaudio.PyAudio", mock_pyaudio_class):
            # Test that concurrent start_recording calls are safe
            results = []

            def start_task():
                result = whisper.start_recording()
                results.append(result)

            threads = [threading.Thread(target=start_task) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Only one thread should successfully start recording
            successful = sum(1 for r in results if r)
            assert successful == 1, "Only one thread should successfully start recording"


class TestAudioThreadSafetyVerification:
    """Verify Audio module already has proper thread safety."""

    def test_audio_has_lock(self):
        """Test that Audio class has a thread safety lock."""
        from distiller_sdk.hardware.audio import Audio

        audio = Audio(auto_check_config=False)

        assert hasattr(audio, "_lock"), "Audio should have a _lock attribute"
        assert isinstance(audio._lock, type(threading.Lock())), (
            "Audio._lock should be a threading.Lock"
        )


class TestCameraThreadSafetyVerification:
    """Verify Camera module already has proper thread safety."""

    def test_camera_has_frame_lock(self, mock_camera_hardware):
        """Test that Camera class has a frame lock."""
        from distiller_sdk.hardware.camera import Camera

        camera = Camera(auto_check_config=False)

        assert hasattr(camera, "_frame_lock"), "Camera should have a _frame_lock attribute"
        assert isinstance(camera._frame_lock, type(threading.Lock())), (
            "Camera._frame_lock should be a threading.Lock"
        )

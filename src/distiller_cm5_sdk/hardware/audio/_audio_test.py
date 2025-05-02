from audio import Audio
import time
audio = Audio(auto_check_config=True)

if audio.check_system_config():
    print("System config is good")
else:
    print("System config is Not Configured")

    
audio.play("test_audio.wav")
audio.set_speaker_volume(60)
print(audio.get_speaker_volume())
time.sleep(5)
audio.stop_playback()

audio.record("test_recording.wav", duration=None)
time.sleep(5)
audio.stop_recording()
audio.play("test_recording.wav")
time.sleep(5)
audio.stop_playback()

audio.close()



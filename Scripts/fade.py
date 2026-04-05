import time
import threading
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

def fade_out_volume(volume, steps=100, delay=0.05):
    """
    Fades out the volume of a specific audio session.
    
    :param volume: The ISimpleAudioVolume object to control.
    :param steps: The number of steps to fade out.
    :param delay: Time delay (in seconds) between steps.
    """
    current_volume = volume.GetMasterVolume()
    print(f"Starting fade-out with initial volume {current_volume:.2f}")

    for i in range(steps, -1, -1):
        new_volume = (i / steps) * current_volume
        volume.SetMasterVolume(new_volume, None)
        time.sleep(delay)

    print("Fade-out complete for this session.")

def fade_out_all_wscripts_concurrently(steps=100, delay=0.05):
    """
    Fades out the volume for all 'wscript.exe' audio sessions concurrently.
    
    :param steps: The number of steps to fade out.
    :param delay: Time delay (in seconds) between steps.
    """
    sessions = AudioUtilities.GetAllSessions()
    threads = []

    for session in sessions:
        if session.Process and session.Process.name().lower() == "wscript.exe":
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            thread = threading.Thread(target=fade_out_volume, args=(volume, steps, delay))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    print("All fade-outs complete.")

# Fade out all wscript.exe sessions concurrently
fade_out_all_wscripts_concurrently(steps=100, delay=0.01)

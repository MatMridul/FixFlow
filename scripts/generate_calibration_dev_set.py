"""Script to generate the Calibration Dev-Set Ground Truth dataset (Task A.2.2)."""
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.calibrator import calibrate_score

DISPLAY_SCENARIOS = [
    ("cal_disp_01", "Screen flickers intermittently at low brightness", ["Adjust Brightness Slider", "Turn Off Adaptive Brightness"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_disp_02", "Adaptive 120Hz refresh rate stuck at 60Hz", ["Enable Adaptive Motion Smoothness"], 1.0, 1.0, 0.9, 1.0, 1),
    ("cal_disp_03", "Dark mode turns on during the day unexpectedly", ["Check Dark Mode Schedule Settings"], 0.9, 1.0, 0.85, 0.9, 1),
    ("cal_disp_04", "Screen turns off too quickly after 15 seconds", ["Increase Screen Timeout to 2 Minutes"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_disp_05", "Text and icons are too small to read", ["Adjust Font Size and Screen Zoom"], 1.0, 1.0, 0.95, 1.0, 1),
    ("cal_disp_06", "Eye comfort shield turns screen yellow", ["Adjust Color Temperature Slider", "Turn Off Eye Comfort Shield"], 1.0, 1.0, 0.9, 0.9, 1),
    ("cal_disp_07", "Display colors look washed out and dull", ["Switch Screen Mode to Vivid"], 1.0, 1.0, 0.8, 1.0, 1),
    ("cal_disp_08", "Always On Display does not show clock when tapped", ["Set Always On Display to Tap to Show"], 1.0, 1.0, 0.95, 1.0, 1),
    ("cal_disp_09", "Screen touch unresponsive with glass screen protector", ["Turn On Touch Sensitivity"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_disp_10", "Edge lighting does not flash for new WhatsApp messages", ["Enable Edge Lighting Style for All Apps"], 0.85, 1.0, 0.8, 0.85, 1),
    ("cal_disp_11", "Pocket touches trigger accidental emergency calls", ["Turn On Accidental Touch Protection"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_disp_12", "Screen resolution changed from QHD+ to FHD+ after gaming", ["Set Screen Resolution to WQHD+"], 1.0, 1.0, 0.9, 1.0, 1),
    ("cal_disp_13", "Brightness drops suddenly in direct sunlight", ["Turn Off Extra Dim", "Enable Adaptive Brightness"], 0.9, 1.0, 0.85, 0.9, 1),
    ("cal_disp_14", "Camera cutout notch cuts off video playback", ["Configure Camera Cutout Per App"], 0.8, 1.0, 0.75, 0.8, 1),
    ("cal_disp_15", "App does not stretch to full screen aspect ratio", ["Set App Aspect Ratio to Full Screen"], 0.85, 1.0, 0.8, 0.9, 1),
    ("cal_disp_16", "One-handed mode gestures not triggering", ["Enable One-Handed Mode Gesture"], 1.0, 1.0, 0.9, 1.0, 1),
    ("cal_disp_17", "Screen saver does not appear when charging on stand", ["Turn On Screen Saver Colors"], 0.75, 0.9, 0.7, 0.8, 1),
    ("cal_disp_18", "Multi-window split screen not allowing all apps", ["Enable Multi Window for All Apps in Labs"], 0.7, 0.8, 0.7, 0.7, 1),
    ("cal_disp_19", "Green vertical line appeared across AMOLED display", ["Visit Authorized Samsung Service Center"], 0.3, 0.5, 0.3, 0.4, 0),
    ("cal_disp_20", "Screen glass physically shattered after dropping on asphalt", ["Schedule Hardware Repair"], 0.2, 0.4, 0.2, 0.3, 0),
]

BATTERY_SCENARIOS = [
    ("cal_batt_01", "Battery draining abnormally fast within 4 hours", ["Enable Power Saving Mode", "Put Unused Apps to Sleep"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_batt_02", "Phone charges very slowly even on 45W charger", ["Turn On Fast Charging in Battery Settings"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_batt_03", "Wireless power share stops charging galaxy watch", ["Ensure Phone Battery Above 30%", "Turn On Wireless Power Sharing"], 1.0, 1.0, 0.9, 0.95, 1),
    ("cal_batt_04", "Battery stops charging at 80% maximum", ["Turn Off Protect Battery or Adjust Limit"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_batt_05", "Background social media apps consuming too much power", ["Add Background Apps to Deep Sleeping Apps"], 1.0, 1.0, 0.95, 1.0, 1),
    ("cal_batt_06", "Adaptive battery not learning usage patterns", ["Turn On Adaptive Battery Toggle"], 1.0, 1.0, 0.85, 0.9, 1),
    ("cal_batt_07", "Overheating during fast charging on hot days", ["Disable Fast Charging While Ambient Temp High"], 0.9, 1.0, 0.85, 0.9, 1),
    ("cal_batt_08", "Battery percentage number missing from status bar", ["Show Battery Percentage in Notification Settings"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_batt_09", "Phone needs daily automatic cleanup", ["Enable Auto Restart in Device Care"], 1.0, 1.0, 0.9, 1.0, 1),
    ("cal_batt_10", "Charging animation and info missing from lock screen", ["Show Charging Information Toggle On"], 1.0, 1.0, 0.85, 0.9, 1),
    ("cal_batt_11", "Moisture detected warning blocks USB charging port", ["Air Dry Port and Clear Android System USB Cache"], 0.8, 0.9, 0.8, 0.85, 1),
    ("cal_batt_12", "Battery level jumps from 20% to 0% abruptly", ["Calibrate Battery Meter via Full Cycle"], 0.7, 0.8, 0.7, 0.75, 1),
    ("cal_batt_13", "Fast wireless charging pad fan too loud at night", ["Turn Off Fast Wireless Charging Overnight"], 0.9, 1.0, 0.85, 0.9, 1),
    ("cal_batt_14", "High background drain from Google Play Services", ["Clear Cache for Google Play Services"], 0.75, 0.85, 0.7, 0.8, 1),
    ("cal_batt_15", "Screen consumes 70% of daily battery capacity", ["Lower Brightness and Shorten Timeout"], 0.95, 1.0, 0.9, 0.95, 1),
    ("cal_batt_16", "GPS navigation drains entire battery on long drives", ["Use Car Charger and Turn Off High Accuracy Scan"], 0.8, 0.9, 0.75, 0.8, 1),
    ("cal_batt_17", "Device warm to touch while idling in pocket", ["Check Device Care for Rogue Background Processes"], 0.85, 0.9, 0.8, 0.85, 1),
    ("cal_batt_18", "Battery health status dropped to Weak in diagnostics", ["Check Battery Status in Samsung Members"], 0.8, 0.85, 0.75, 0.8, 1),
    ("cal_batt_19", "Battery swollen and pushing back glass panel open", ["Stop Charging Immediately and Contact Service Center"], 0.2, 0.4, 0.2, 0.3, 0),
    ("cal_batt_20", "Liquid spilled into USB-C port while phone was plugged in", ["Power Down Phone and Dry Completely"], 0.3, 0.5, 0.3, 0.4, 0),
]

CONNECTIVITY_SCENARIOS = [
    ("cal_conn_01", "Wi-Fi disconnects frequently every few minutes", ["Forget and Reconnect to Wi-Fi Network", "Turn Off Intelligent Wi-Fi Switch"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_conn_02", "Bluetooth headphones audio cuts out and stutters", ["Unpair and Re-pair Bluetooth Device", "Clear Bluetooth System Cache"], 1.0, 1.0, 0.95, 1.0, 1),
    ("cal_conn_03", "Mobile hotspot turns off automatically after 10 minutes", ["Change Hotspot Timeout to Never"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_conn_04", "Mobile data icon shows exclamation mark with no internet", ["Toggle Airplane Mode", "Reset APN Access Point Names"], 1.0, 1.0, 0.9, 0.95, 1),
    ("cal_conn_05", "All network connections corrupted after update", ["Reset Network Settings in General Management"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_conn_06", "Wi-Fi calling toggle disabled by carrier", ["Turn On Wi-Fi Calling in Phone App Settings"], 0.95, 1.0, 0.9, 0.95, 1),
    ("cal_conn_07", "Quick Share cannot find nearby Galaxy devices", ["Set Quick Share Visibility to Anyone Nearby"], 1.0, 1.0, 0.95, 1.0, 1),
    ("cal_conn_08", "Private DNS server cannot be accessed error", ["Set Private DNS to Automatic or Turn Off"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_conn_09", "NFC Google Pay contactless payment terminal rejected", ["Set Default Payment App to Google Wallet", "Ensure NFC Turned On"], 1.0, 1.0, 0.9, 1.0, 1),
    ("cal_conn_10", "VoLTE calls dropping when switching cell towers", ["Verify VoLTE Enabled in Mobile Networks"], 0.85, 0.9, 0.8, 0.85, 1),
    ("cal_conn_11", "Airplane mode switch stuck in grayed out state", ["Restart Device in Safe Mode to Isolate Radio Crash"], 0.8, 0.9, 0.75, 0.8, 1),
    ("cal_conn_12", "5G connection drains battery without speed boost", ["Change Network Mode to LTE 3G 2G Auto"], 1.0, 1.0, 0.95, 1.0, 1),
    ("cal_conn_13", "eSIM profile not activating after scanning QR code", ["Check SIM Card Manager and Re-scan Profile"], 0.85, 0.9, 0.8, 0.85, 1),
    ("cal_conn_14", "Dual SIM not switching mobile data automatically", ["Enable Auto Data Switching in SIM Manager"], 0.9, 1.0, 0.9, 0.9, 1),
    ("cal_conn_15", "Bluetooth pairing rejected due to wrong PIN", ["Delete Device from Both Ends and Retry Pairing"], 0.9, 0.95, 0.85, 0.9, 1),
    ("cal_conn_16", "Wi-Fi 6GHz 6E network SSID not visible in scan list", ["Verify Router 6GHz WPA3 Security Compatibility"], 0.75, 0.8, 0.7, 0.75, 1),
    ("cal_conn_17", "Android Auto wireless disconnects at toll plazas", ["Switch to High Quality USB Cable for Android Auto"], 0.7, 0.8, 0.7, 0.75, 1),
    ("cal_conn_18", "Smart View screen mirroring lags behind TV audio", ["Change Aspect Ratio on Phone in Smart View"], 0.8, 0.85, 0.75, 0.8, 1),
    ("cal_conn_19", "SIM card tray physically broken inside phone slot", ["Do Not Probe Slot and Contact Repair Center"], 0.25, 0.4, 0.2, 0.3, 0),
    ("cal_conn_20", "Cellular baseband antenna completely detached after drop", ["Visit Hardware Technician for Board Repair"], 0.2, 0.3, 0.2, 0.3, 0),
]

SOUND_SYSTEM_SCENARIOS = [
    ("cal_sys_01", "Speaker crackles at high volumes when playing music", ["Turn Off Dolby Atmos Equalizer Bass Boost", "Clean Speaker Grill"], 0.9, 1.0, 0.9, 0.95, 1),
    ("cal_sys_02", "No sound from speaker during incoming voice calls", ["Check Sound Mode is Set to Sound not Mute", "Turn Up Ringtone Volume"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_sys_03", "Notification sounds completely silent for text messages", ["Set App Notification Category to Alerting"], 1.0, 1.0, 0.95, 1.0, 1),
    ("cal_sys_04", "Do Not Disturb schedule turns on during workday", ["Review and Delete Unwanted DND Schedules"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_sys_05", "Dolby Atmos sound equalizer presets locked", ["Connect Headphones to Unlock Dolby Atmos"], 0.85, 0.95, 0.8, 0.9, 1),
    ("cal_sys_06", "Separate app sound playing Spotify on phone speaker instead of car", ["Configure Separate App Sound Audio Device"], 0.95, 1.0, 0.9, 0.95, 1),
    ("cal_sys_07", "Vibration intensity too weak to feel in pocket", ["Increase Call and Notification Vibration Intensity"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_sys_08", "Volume rocker keys control ringtone instead of media", ["Enable Use Volume Keys for Media"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_sys_09", "Microphone muffled during speakerphone conference calls", ["Clean Top Secondary Microphone Hole"], 0.75, 0.85, 0.7, 0.8, 1),
    ("cal_sys_10", "Phone restarts into bootloop after third-party launcher install", ["Reboot into Safe Mode and Uninstall Launcher"], 0.85, 0.9, 0.8, 0.85, 1),
    ("cal_sys_11", "System cache corrupted causing stuttering animations", ["Wipe Cache Partition from Recovery Menu"], 0.8, 0.85, 0.75, 0.8, 1),
    ("cal_sys_12", "Phone automatically restarts during business presentations", ["Adjust Scheduled Auto Restart Time in Device Care"], 1.0, 1.0, 0.95, 1.0, 1),
    ("cal_sys_13", "Camera app crashes immediately upon opening", ["Clear Storage and Cache for Camera App"], 1.0, 1.0, 0.9, 1.0, 1),
    ("cal_sys_14", "Lift to wake motion gesture triggers too easily in hand", ["Turn Off Lift to Wake in Motions and Gestures"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_sys_15", "Lock screen clock font style reset to default", ["Customize Lock Screen Clock Font in Wallpaper Settings"], 0.9, 1.0, 0.85, 0.9, 1),
    ("cal_sys_16", "App permission denied popup blocks opening gallery", ["Grant Storage and Photos Permission in App Info"], 1.0, 1.0, 0.95, 1.0, 1),
    ("cal_sys_17", "Software update download stuck at 99 percent", ["Clear Cache for Software Update System App"], 0.8, 0.85, 0.75, 0.8, 1),
    ("cal_sys_18", "Side power key double press opens Bixby instead of camera", ["Set Side Key Double Press to Quick Launch Camera"], 1.0, 1.0, 1.0, 1.0, 1),
    ("cal_sys_19", "Earpiece speaker diaphragm punctured with sharp pin", ["Replace Earpiece Speaker Component"], 0.2, 0.3, 0.2, 0.3, 0),
    ("cal_sys_20", "Motherboard power IC burnt out from water immersion", ["Submit for Motherboard Repair"], 0.15, 0.3, 0.15, 0.25, 0),
]


def generate_dataset():
    all_data = []

    groups = [
        ("display", DISPLAY_SCENARIOS),
        ("battery", BATTERY_SCENARIOS),
        ("connectivity", CONNECTIVITY_SCENARIOS),
        ("sound_system", SOUND_SYSTEM_SCENARIOS),
    ]

    for domain_name, scenarios in groups:
        for scen_id, query, action_titles, g_cov, v_pass, r_marg, p_align, label in scenarios:
            score = calibrate_score(
                grounding_coverage=g_cov,
                validator_pass_rate=v_pass,
                retrieval_margin=r_marg,
                path_alignment=p_align,
            )

            actions = [
                {"actionTitle": title, "category": "manual" if "Center" in title or "Technician" in title else "auto"}
                for title in action_titles
            ]

            all_data.append({
                "id": scen_id,
                "domain": domain_name,
                "query": query,
                "ground_truth_actions": actions,
                "grounding_coverage": g_cov,
                "validator_pass_rate": v_pass,
                "retrieval_margin": r_marg,
                "path_alignment": p_align,
                "expected_calibrated_score": score,
                "label": label,
            })

    output_path = Path(__file__).resolve().parent.parent / "data" / "calibration_dev_set.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2)

    print(f"Generated {len(all_data)} calibration scenarios at {output_path}")


if __name__ == "__main__":
    generate_dataset()

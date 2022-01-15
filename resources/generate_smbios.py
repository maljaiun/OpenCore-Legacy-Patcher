from data import smbios_data, os_data, cpu_data
from resources import utilities


def set_smbios_model_spoof(model):
    try:
        smbios_data.smbios_dictionary[model]["Screen Size"]
        # Found mobile SMBIOS
        if model.startswith("MacBookAir"):
            if smbios_data.smbios_dictionary[model]["Screen Size"] == 13:
                return "MacBookAir7,2"
            elif smbios_data.smbios_dictionary[model]["Screen Size"] == 11:
                return "MacBookAir7,1"
            else:
                # Unknown Model
                raise Exception(f"Unknown SMBIOS for spoofing: {model}")
        elif model.startswith("MacBookPro"):
            if smbios_data.smbios_dictionary[model]["Screen Size"] == 13:
                return "MacBookPro12,1"
            elif smbios_data.smbios_dictionary[model]["Screen Size"] >= 15:
                # 15" and 17"
                try:
                    smbios_data.smbios_dictionary[model]["Switchable GPUs"]
                    return "MacBookPro11,5"
                except KeyError:
                    return "MacBookPro11,4"
            else:
                # Unknown Model
                raise Exception(f"Unknown SMBIOS for spoofing: {model}")
        elif model.startswith("MacBook"):
            if smbios_data.smbios_dictionary[model]["Screen Size"] == 13:
                return "MacBookAir7,2"
            elif smbios_data.smbios_dictionary[model]["Screen Size"] == 12:
                return "MacBook9,1"
            else:
                # Unknown Model
                raise Exception(f"Unknown SMBIOS for spoofing: {model}")
        else:
            # Unknown Model
            raise Exception(f"Unknown SMBIOS for spoofing: {model}")
    except KeyError:
        # Found desktop model
        if model.startswith("MacPro") or model.startswith("Xserve"):
            return "MacPro7,1"
        elif model.startswith("Macmini"):
            return "Macmini7,1"
        elif model.startswith("iMac"):
            if smbios_data.smbios_dictionary[model]["Max OS Supported"] <= os_data.os_data.high_sierra:
                # Models dropped in Mojave either do not have an iGPU, or should have them disabled
                return "iMacPro1,1"
            else:
                return "iMac17,1"
        else:
            # Unknown Model
            raise Exception(f"Unknown SMBIOS for spoofing: {model}")


def update_firmware_features(firmwarefeature):
    # Adjust FirmwareFeature to support everything macOS requires
    # APFS Bit (19/20): 10.13+ (OSInstall)
    # Large BaseSystem Bit (35): 12.0 B7+ (patchd)
    # https://github.com/acidanthera/OpenCorePkg/tree/2f76673546ac3e32d2e2d528095fddcd66ad6a23/Include/Apple/IndustryStandard/AppleFeatures.h
    firmwarefeature |= 2 ** 19  # FW_FEATURE_SUPPORTS_APFS
    firmwarefeature |= 2 ** 20  # FW_FEATURE_SUPPORTS_APFS_EXTRA
    firmwarefeature |= 2 ** 35  # FW_FEATURE_SUPPORTS_LARGE_BASESYSTEM
    return firmwarefeature


def generate_fw_features(model, custom):
    if not custom:
        firmwarefeature = utilities.get_rom("firmware-features")
        if not firmwarefeature:
            print("- Failed to find FirmwareFeatures, falling back on defaults")
            if smbios_data.smbios_dictionary[model]["FirmwareFeatures"] is None:
                firmwarefeature = 0
            else:
                firmwarefeature = int(smbios_data.smbios_dictionary[model]["FirmwareFeatures"], 16)
    else:
        if smbios_data.smbios_dictionary[model]["FirmwareFeatures"] is None:
            firmwarefeature = 0
        else:
            firmwarefeature = int(smbios_data.smbios_dictionary[model]["FirmwareFeatures"], 16)
    firmwarefeature = update_firmware_features(firmwarefeature)
    return firmwarefeature


def find_model_off_board(board):
    # Find model based off Board ID provided
    # Return none if unknown

    # Strip extra data from Target Types (ap, uppercase)
    if not (board.startswith("Mac-") or board.startswith("VMM-")):
        if board.lower().endswith("ap"):
            board = board[:-2]
        board = board.lower()

    for key in smbios_data.smbios_dictionary:
        if board in [smbios_data.smbios_dictionary[key]["Board ID"], smbios_data.smbios_dictionary[key]["SecureBootModel"]]:
            if key.endswith("_v2") or key.endswith("_v3") or key.endswith("_v4"):
                # smbios_data has duplicate SMBIOS to handle multiple board IDs
                key = key[:-3]
            if key == "MacPro4,1":
                # 4,1 and 5,1 have the same board ID, best to return the newer ID
                key = "MacPro5,1"
            return key
    return None

def check_firewire(model):
    # MacBooks never supported FireWire
    # Pre-Thunderbolt MacBook Airs as well
    if model.startswith("MacBookPro"):
        return True
    elif model.startswith("MacBookAir"):
        if smbios_data.smbios_dictionary[model]["CPU Generation"] < cpu_data.cpu_data.sandy_bridge.value:
            return False
    elif model.startswith("MacBook"):
        return False
    else:
        return True
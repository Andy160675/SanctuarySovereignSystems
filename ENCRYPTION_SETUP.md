# 🔐 SOVEREIGN ENCRYPTION PROTOCOL

## 1. WINDOWS (BitLocker)

**Objective:** Encrypt Data Drives (D: and E:) with AES-256.

1.  **Open PowerShell as Admin.**
2.  **Check Status:**
    ```powershell
    manage-bde -status
    ```
3.  **Encrypt Drive D:**
    ```powershell
    # Enable BitLocker with Password Protector
    Enable-BitLocker -MountPoint "D:" -EncryptionMethod XtsAes256 -UsedSpaceOnly -PasswordProtector
    ```
    *Enter a strong, unique passphrase when prompted.*
4.  **Encrypt Drive E:**
    ```powershell
    Enable-BitLocker -MountPoint "E:" -EncryptionMethod XtsAes256 -UsedSpaceOnly -PasswordProtector
    ```
5.  **Save Recovery Keys:**
    *   Print the recovery keys.
    *   Store one copy in a physical safe.
    *   Store one copy in a separate, offline location.

## 2. LINUX (LUKS)

**Objective:** Encrypt External USB/SATA Drives.

1.  **Identify Drive:**
    ```bash
    lsblk
    # Assume /dev/sdb is the target
    ```
2.  **Format & Encrypt:**
    ```bash
    sudo cryptsetup luksFormat /dev/sdb
    # Type YES and enter passphrase
    ```
3.  **Open Volume:**
    ```bash
    sudo cryptsetup luksOpen /dev/sdb sovereign_data
    ```
4.  **Create Filesystem:**
    ```bash
    sudo mkfs.ext4 /dev/mapper/sovereign_data
    ```
5.  **Mount:**
    ```bash
    sudo mkdir /mnt/sovereign
    sudo mount /dev/mapper/sovereign_data /mnt/sovereign
    ```

## 3. VERIFICATION

Before deploying the Sovereign System, verify that all data drives are locked upon reboot and require manual intervention (passphrase) to mount. This ensures data at rest is secure if hardware is seized.

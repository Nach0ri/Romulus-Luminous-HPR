# Headless usage — Luminous-HPR

Short notes for running the IMU + Camera tools headless on a Raspberry Pi.

Files of interest
- `check_headless_requirements.py` — verifies Python modules, device nodes, and commands before hardware init.
- `launch_capture.py` — monitors the LSM6DSOX for a >3G event and captures one image per second for 120s.
- `camera_imu_test_gui.py` — GUI test tool (requires a display).

Quick requirements
- Enable I2C and Camera (via `sudo raspi-config` or `raspi-config nonint`).
- Install dependencies (installer script created earlier attempts this):

```bash
sudo python3 install_rpi_dependencies.py
```

Running headless
- To run normally (the checker runs first):

```bash
sudo python3 launch_capture.py
```

- To run while bypassing the pre-check (useful in headless setups where you manage dependencies yourself):

```bash
```bash
# environment variable
sudo SKIP_HEADLESS_CHECK=1 python3 launch_capture.py

# or CLI flag
sudo python3 launch_capture.py --skip-check
```
```

Autostart suggestion (systemd)
- Create a `systemd` unit that calls `launch_capture.py --skip-check` if you prefer the service to run at boot without the interactive check. Ensure the service runs as a user in `i2c,video` or run it with `sudo`.

Install helper
- A helper script is included to install and enable a systemd service from this repository. Run from the repository directory on the Pi with `sudo`:

```bash
sudo ./install_impact_service.sh
```

This writes `/etc/systemd/system/launch_capture.service`, enables and starts it, and configures the service to run `launch_capture.py --skip-check` from the repository directory.

Notes
- Filenames use the system clock; ensure the Pi clock is set if you need accurate timestamps.
- The script writes captures to `impact_captures/` in the current working directory; ensure sufficient disk space.
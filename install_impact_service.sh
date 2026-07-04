#!/usr/bin/env sh
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run with sudo from the repository directory"
  echo "Usage: sudo ./install_impact_service.sh"
  exit 1
fi

DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$DIR/launch_capture.py"

if [ ! -f "$SCRIPT" ]; then
  echo "launch_capture.py not found in $DIR"
  exit 1
fi

UNIT_PATH=/etc/systemd/system/launch_capture.service

cat > "$UNIT_PATH" <<EOF
[Unit]
Description=Impact Capture (IMU-triggered camera capture)
After=network.target

[Service]
Type=simple
Environment=SKIP_HEADLESS_CHECK=1
ExecStart=/usr/bin/python3 $SCRIPT --skip-check
WorkingDirectory=$DIR
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now launch_capture.service

echo "Installed and started launch_capture.service"
echo "To view logs: sudo journalctl -u launch_capture.service -f"

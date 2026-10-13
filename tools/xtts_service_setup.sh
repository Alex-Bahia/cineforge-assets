#!/bin/bash
# =============================================================================
# XTTS v2 — Configurar como serviço systemd (auto-start)
# Rodar APÓS instalar_xtts_vps.sh
# =============================================================================

echo "[systemd] Criando serviço xtts-api..."

sudo tee /etc/systemd/system/xtts-api.service > /dev/null << 'EOF'
[Unit]
Description=CineForge Voice API (XTTS v2)
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/home/ubuntu/venv_xtts/bin/python3 /home/ubuntu/xtts_api.py
Restart=always
RestartSec=10
Environment="HOME=/home/ubuntu"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable xtts-api
sudo systemctl start xtts-api

echo ""
echo "Status do serviço:"
sudo systemctl status xtts-api --no-pager

echo ""
echo "========================================"
echo "  Serviço ativado! Comandos úteis:"
echo "  sudo systemctl status xtts-api"
echo "  sudo systemctl restart xtts-api"
echo "  sudo journalctl -u xtts-api -f  (logs ao vivo)"
echo "========================================"

# Abrir porta 8765 no firewall (Oracle Cloud usa iptables)
echo ""
echo "[firewall] Abrindo porta 8765..."
sudo iptables -I INPUT -p tcp --dport 8765 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null 2>&1 || true
echo "Porta 8765 liberada."

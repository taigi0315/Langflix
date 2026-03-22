#!/bin/bash
# Run this ONCE on a fresh EC2 instance to set everything up
# Usage: bash ec2-first-setup.sh <YOUR_GEMINI_API_KEY>

set -e

GEMINI_API_KEY="${1:-}"
if [ -z "$GEMINI_API_KEY" ]; then
  echo "Usage: bash ec2-first-setup.sh <YOUR_GEMINI_API_KEY>"
  exit 1
fi

echo "=== LangFlix EC2 Setup ==="

# 1. System packages
echo "[1/6] Installing system packages..."
sudo yum update -y
sudo yum install -y git

# 2. Docker
echo "[2/6] Installing Docker..."
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# 3. Docker Compose plugin
echo "[3/6] Installing Docker Compose..."
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# 4. Data directories (acts as EBS storage)
echo "[4/6] Creating data directories..."
sudo mkdir -p /data/output /data/logs /data/assets
sudo chown -R ec2-user:ec2-user /data

# 5. Clone the repo
echo "[5/6] Cloning LangFlix repository..."
cd /home/ec2-user
if [ ! -d "Langflix" ]; then
  git clone https://github.com/taigi0315/Langflix.git
fi
cd Langflix

# 6. Create .env file
echo "[6/6] Creating .env file..."
cat > .env << EOF
GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=gemini-2.5-flash
LANGFLIX_OUTPUT_DIR=/data/output
LANGFLIX_LOG_DIR=/data/logs
LANGFLIX_LOG_LEVEL=INFO
EOF

# Create a minimal config if it doesn't exist
mkdir -p config
if [ ! -f config/config.yaml ]; then
  echo "# LangFlix config - override defaults here" > config/config.yaml
fi

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "IMPORTANT: Log out and back in for docker group to take effect, then run:"
echo ""
echo "  cd /home/ec2-user/Langflix/deploy"
echo "  docker compose -f docker-compose.ec2.yml up --build -d"
echo ""
echo "App will be available at:"
echo "  FastAPI: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "  Health:  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/health"

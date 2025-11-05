#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════
MODEL="codellama:13b"           # Change this to test different models
OLLAMA_URL="http://localhost:11434/api/chat"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
cat << "EOF"
    __    __    __  ______           ____                            __            
   / /   / /   /  |/  /  _/___  _____/ __ \___  _____/ /_____  _____/ /_____  _____
  / /   / /   / /|_/ // // __ \/ ___/ /_/ / _ \/ ___/ __/ __ \/ ___/ __/ __ \/ ___/
 / /___/ /___/ /  / // // / / (__  ) ____/  __/ /__/ /_/ /_/ / /  / /_/ /_/ / /    
/_____/_____/_/  /_/___/_/ /_/____/_/    \___/\___/\__/\____/_/   \__/\____/_/     
                                                                                     
EOF
echo -e "${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                       🔍  Live Demo - Security Testing  🔒                ${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Target Model:${NC} ${MODEL}  |  ${CYAN}Endpoint:${NC} ${OLLAMA_URL}"
echo ""

# Demo 1: Identification
echo -e "${YELLOW}[1/2] Identifying Model...${NC}"
echo -e "${CYAN}$ python3 llmfinder.py --url ${OLLAMA_URL} --model-in-payload ${MODEL} --no-embeddings\n"
python3 llmfinder.py \
  --url "${OLLAMA_URL}" \
  --model-in-payload "${MODEL}" \
  --no-embeddings \
  2>&1

echo -e "${GREEN}✓ Identification complete${NC}\n"
sleep 2

# Demo 2: Pentesting
echo -e "${YELLOW}[2/2] Running Security Tests...${NC}"
REPORT_FILE="demo_report_$(date +%Y%m%d_%H%M%S).json"
echo -e "${CYAN}$ python3 llmpentester.py --url ${OLLAMA_URL} --model-in-payload ${MODEL} --output-file ${REPORT_FILE}\n"
python3 llmpentester.py \
  --url "${OLLAMA_URL}" \
  --model-in-payload "${MODEL}" \
  --output-file "$REPORT_FILE" \
  2>&1

echo -e "${GREEN}✓ Security tests complete${NC}\n"

echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                           ✅  Demo Complete!  ✅                           ${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}\n"

# Mostrar reportes generados
echo -e "${CYAN}📊 Generated Reports:${NC}"
ls -lh demo_report_*.json 2>/dev/null || echo "  No reports found"
echo -e "\n${CYAN}💡 Tip:${NC} View report with: ${YELLOW}cat demo_report_*.json | jq '.'${NC}"
echo ""
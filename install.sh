#!/usr/bin/env bash
#
# TubeX Installer for Arch Linux
# Installs dependencies via pacman and sets up the 'tubex' alias.

set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}${BOLD}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}${BOLD}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}${BOLD}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}${BOLD}[ERROR]${NC} $1" >&2
}

echo -e "${CYAN}${BOLD}"
echo "  _____      _        __   __"
echo " |_   _|   _| |__   __\ \ / /"
echo "   | || | | | '_ \ / _ \ V / "
echo "   | || |_| | |_) |  __// . \ "
echo "   |_| \__,_|_.__/ \___/_/ \_\\"
echo "   Arch Linux Installer"
echo -e "${NC}"

# If running through a pipe (e.g. curl | bash), reconnect stdin to terminal for interactive prompts
if [[ ! -t 0 ]] && [[ -r /dev/tty ]]; then
    exec < /dev/tty
fi

# 1. Verify Arch Linux / pacman
if ! command -v pacman &>/dev/null; then
    error "pacman was not found. This install script is tailored for Arch Linux and Arch-based distributions."
    exit 1
fi

# 2. Identify script location or clone repository if piped via curl
REPO_URL="https://github.com/DevBarik731/Tubex.git"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
TUBEX_FILE="${SCRIPT_DIR}/tubex.py"

if [[ ! -f "$TUBEX_FILE" ]]; then
    INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/tubex"
    info "Repository not found locally. Cloning TubeX into '${INSTALL_DIR}'..."
    if ! command -v git &>/dev/null; then
        info "Installing git..."
        if [[ $EUID -eq 0 ]]; then
            pacman -S --needed --noconfirm git
        elif command -v sudo &>/dev/null; then
            sudo pacman -S --needed --noconfirm git
        fi
    fi
    mkdir -p "$(dirname "$INSTALL_DIR")"
    if [[ -d "${INSTALL_DIR}/.git" ]]; then
        git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || true
    else
        rm -rf "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
    TUBEX_FILE="${INSTALL_DIR}/tubex.py"
fi

if [[ ! -f "$TUBEX_FILE" ]]; then
    error "Could not find or clone tubex.py at '${TUBEX_FILE}'."
    exit 1
fi

# Ensure tubex.py is executable
chmod +x "$TUBEX_FILE"

# 3. Check and install dependencies
DEPENDENCIES=("python" "python-textual" "yt-dlp" "mpv")
MISSING_DEPS=()

info "Checking dependencies..."
for pkg in "${DEPENDENCIES[@]}"; do
    if pacman -Q "$pkg" &>/dev/null; then
        echo -e "  - ${pkg}: ${GREEN}installed${NC}"
    else
        echo -e "  - ${pkg}: ${YELLOW}missing${NC}"
        MISSING_DEPS+=("$pkg")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    info "Installing missing dependencies: ${MISSING_DEPS[*]}"
    if [[ $EUID -eq 0 ]]; then
        pacman -S --needed --noconfirm "${MISSING_DEPS[@]}"
    elif command -v sudo &>/dev/null; then
        sudo pacman -S --needed --noconfirm "${MISSING_DEPS[@]}"
    else
        error "Root privileges or sudo is required to install dependencies via pacman."
        echo "Please run: sudo pacman -S --needed ${MISSING_DEPS[*]}"
        exit 1
    fi
    success "All dependencies have been installed successfully."
else
    success "All dependencies are already satisfied."
fi

# 4. Set up the 'tubex' alias and local symlink
ALIAS_CMD="alias tubex=\"python3 '${TUBEX_FILE}'\""
UPDATED_SHELLS=()

configure_rc_file() {
    local rc_file="$1"
    local shell_name="$2"

    if [[ -f "$rc_file" ]]; then
        if grep -q "alias tubex=" "$rc_file" 2>/dev/null; then
            sed -i "s|alias tubex=.*|${ALIAS_CMD}|" "$rc_file"
            UPDATED_SHELLS+=("${shell_name} (${rc_file}) [updated]")
        else
            {
                echo ""
                echo "# TubeX - Terminal YouTube Player"
                echo "${ALIAS_CMD}"
            } >> "$rc_file"
            UPDATED_SHELLS+=("${shell_name} (${rc_file}) [added]")
        fi
    fi
}

# Configure for zsh and bash if their rc files exist
configure_rc_file "$HOME/.zshrc" "Zsh"
configure_rc_file "$HOME/.bashrc" "Bash"

# Configure for fish if fish directory or config exists
if [[ -d "$HOME/.config/fish" ]]; then
    FISH_CONFIG="$HOME/.config/fish/config.fish"
    mkdir -p "$HOME/.config/fish"
    if [[ -f "$FISH_CONFIG" ]] && grep -q "alias tubex" "$FISH_CONFIG" 2>/dev/null; then
        sed -i "s|alias tubex .*|alias tubex 'python3 ${TUBEX_FILE}'|" "$FISH_CONFIG"
        UPDATED_SHELLS+=("Fish (${FISH_CONFIG}) [updated]")
    else
        {
            echo ""
            echo "# TubeX - Terminal YouTube Player"
            echo "alias tubex 'python3 ${TUBEX_FILE}'"
        } >> "$FISH_CONFIG"
        UPDATED_SHELLS+=("Fish (${FISH_CONFIG}) [added]")
    fi
fi

# Also create ~/.local/bin/tubex symlink for PATH availability
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"
ln -sf "$TUBEX_FILE" "${LOCAL_BIN}/tubex"

# 5. Summary / Instructions
echo ""
success "TubeX installation complete!"
echo ""
echo -e "${BOLD}Alias configured in:${NC}"
for item in "${UPDATED_SHELLS[@]}"; do
    echo -e "  ✓ ${item}"
done
echo -e "  ✓ Direct executable link: ${LOCAL_BIN}/tubex"
echo ""

CURRENT_SHELL_NAME="$(basename "${SHELL:-bash}")"
case "$CURRENT_SHELL_NAME" in
    zsh)
        RELOAD_CMD="source ~/.zshrc"
        ;;
    bash)
        RELOAD_CMD="source ~/.bashrc"
        ;;
    fish)
        RELOAD_CMD="source ~/.config/fish/config.fish"
        ;;
    *)
        RELOAD_CMD="source ~/.bashrc"
        ;;
esac

echo -e "${BOLD}To start using TubeX immediately, run:${NC}"
echo -e "  ${CYAN}${RELOAD_CMD}${NC}"
echo -e "  ${CYAN}tubex${NC}"
echo ""
echo -e "Or simply open a new terminal window and type ${BOLD}tubex${NC}."

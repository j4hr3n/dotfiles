# Ghostty Configuration

This directory contains configuration files for [Ghostty](https://ghostty.org/), a modern terminal emulator.

## Files

- `config`: The main Ghostty configuration file

## Installation

The configuration is automatically symlinked to the appropriate location by the dotfiles installer:

```
~/Library/Application Support/com.mitchellh.ghostty/config → configs/ghostty/config
```

## Manual Setup

If you need to set up the symlink manually:

```bash
mkdir -p ~/Library/Application\ Support/com.mitchellh.ghostty/
ln -sf $(pwd)/configs/ghostty/config ~/Library/Application\ Support/com.mitchellh.ghostty/config
```

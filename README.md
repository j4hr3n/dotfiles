# $HOME sweet $HOME

## Configuration

To update and symlink the different folders [dotbot](https://github.com/anishathalye/dotbot) is used!

## Brew, Bundle, and Brewfile

https://gist.github.com/ChristopherA/a579274536aab36ea9966f301ff14f3f

## Setup

To install `dotfiles` run the appropriate installer.

### Windows

```pwsh
powershell -NoProfile -ExecutionPolicy unrestricted -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; &([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing 'https://raw.github.com/andeki92/dotfiles/main/meta/profiles/windows/setup.ps1')))"
```

Native Windows symlinks are only created on Windows Vista/2008 and later, and only on filesystems supporting reparse points like NTFS. In order to maintain backwards compatibility, users must explicitely requests creating them. This is done by setting the environment variable for MSYS to contain the string winsymlinks:native or winsymlinks:nativestrict. Without this setting, 'ln -s' may copy the file instead of making a link to it.

In order enable these symbolic links, run git bash as administrator, then:

```
export MSYS=winsymlinks:nativestrict
./install-profile windows
```

### Mac / WSL2

```zsh
# If you have curl installed ########################################
curl -Ls https://raw.githubusercontent.com/j4hr3n/dotfiles/main/setup | bash

# If you have wget installed ########################################
wget -q -O - https://raw.githubusercontent.com/j4hr3n/dotfiles/main/setup | bash
```

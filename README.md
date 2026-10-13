# WAN / LAN Switch for GL-MT3000

A small LuCI add-on that swaps the WAN and LAN Ethernet sockets on the **GL.iNet GL-MT3000 (Beryl AX)**. It implements the [GL.iNet forum port-swap workaround](https://forum.gl-inet.com/t/gl-mt3000-wan-port-cable-not-detected/37957/7) through an authenticated web page.

- **Original ports:** WAN socket for internet, LAN socket for the local network.
- **Swapped ports:** LAN socket for internet, WAN socket for the local network.
- Shows the current port roles, Ethernet carrier/speed and WAN address; status refreshes automatically.
- Saves backups, supports confirmation and undo, and restores an unconfirmed change after two minutes.
- Restores an interrupted, unconfirmed change at boot before networking starts.
- Uses the existing LuCI root login and CSRF protection; no extra password is stored.

## Compatibility

Verified on **GL-MT3000, GL.iNet firmware 4.11.0, OpenWrt 21.02-SNAPSHOT** with Lua-based LuCI. Other router models and newer LuCI architectures have not been tested. The helper rejects other models.

The supported layout has one bare Ethernet interface (`eth0` or `eth1`) as WAN and the other in `br-lan`, with a static management LAN. Wi-Fi and unrelated bridge members are preserved. **Ethernet VLAN subinterfaces inside `br-lan` are unsupported; do not use this add-on with that layout.** Some conflicting custom layouts are rejected, but this is not a general VLAN editor.

## Install

Download `luci-app-port-switch_1.0.0_all.ipk` from the [latest release](https://github.com/4781jicsa020Chandler/luci-app-port-switch/releases/latest).

Install LuCI through GL.iNet's Advanced Settings page. If installing from SSH instead:

```sh
opkg update
opkg install luci
/etc/init.d/rpcd enable
/etc/init.d/rpcd start
```

Upload the downloaded installer to `/tmp` on the router, then run:

```sh
opkg install /tmp/luci-app-port-switch_1.0.0_all.ipk
```

Open **LuCI → Network → WAN / LAN Switch**, or visit:

```text
http://192.168.8.1/cgi-bin/luci/admin/network/port-switch
```

Use the router's actual LAN address if it differs. Sign in as `root` with the router admin password.

## Use

1. Connect to the router over **Wi-Fi** before switching.
2. Choose **Original ports** or **Swapped ports**, then click **Apply port roles**.
3. Move the internet cable to the selected socket.
4. Click **Keep new port roles** within two minutes, or click **Undo switch**.

If you do not confirm, the previous network configuration returns automatically. The management LAN keeps its address. IPv6 references to `@wan` are preserved; direct references to the old Ethernet WAN interface are moved with it.

GL.iNet's main Ethernet controls, a factory reset, or switching operating mode can replace these settings. Refresh this page after using those controls. Port switching updates only the network configuration and does not rewrite vendor capability flags.

## Backups and removal

Backups are stored under `/etc/port-switch/backups/`, with the five most recent normally retained. The active rollback backup is always protected. To remove the add-on:

```sh
opkg remove luci-app-port-switch
```

Confirmed port roles and saved backups remain. A pending switch must be rolled back successfully before the package is removed.

For GL.iNet's nginx web interface, installation selects LuCI's authenticated CGI transport if its default RPC path points at the vendor UI. The previous LuCI configuration is saved at `/etc/port-switch/luci-before-port-switch`.

## Build and checks

Python 3.9+ is sufficient; no OpenWrt SDK or compiled router binary is needed.

```sh
python3 build.py
python3 -m unittest discover -s tests -v
```

Artifacts are written to `dist/`. Use `--output-dir /your/output/folder` to choose another destination. The source ZIP includes only project source and documentation, excluding Git metadata, build outputs and caches.

The router backend was tested with native ash, UCI, jshn and jsonfilter against isolated network fixtures: both switch directions, runtime confirmation, IPv6 handling, preservation of unrelated settings, automatic/manual rollback, boot recovery and invalid-input rejection. The installed page and its status display were also verified on the GL-MT3000. GitHub Actions checks packaging and shell syntax; it does not connect to a router.

## License

[MIT](LICENSE).

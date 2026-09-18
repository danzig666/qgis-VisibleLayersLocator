# Visible Layers Locator (prefix: `vls`)

A tiny QGIS plugin that registers a Locator filter to search **only among effectively visible layers** in the current project.
Selecting a result selects the layer in the Layers panel.

Compatible with **QGIS 3.4+ (Qt5)** and **QGIS 4.x (Qt6)**.

## Usage
- In the Locator bar (`Ctrl+K`), type: `vls <part of layer name>`
- Example: `vls roads`

> QGIS ignores locator prefixes shorter than 3 characters for plugin filters, which is why the prefix is `vls`.

## Install
1. Copy this folder into your QGIS profile's `python/plugins/` folder as `VisibleLayersLocator`
   (or zip it and use **Plugins → Manage and Install Plugins… → Install from ZIP**).
2. Restart QGIS, then enable the plugin in **Plugins → Manage and Install Plugins...**.

## Notes
- A layer is "effectively visible" when it and all of its parent groups are checked.
- The layer tree is snapshotted on the main thread (`prepare()`), and matching runs in the locator's worker thread.
- Tested headless on QGIS 3.4, 3.10, 3.14, 3.26, 3.40, 3.44 and 4.2.

## License
GNU General Public License v2.0 or later — see [LICENSE](LICENSE).

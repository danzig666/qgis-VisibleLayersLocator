# -*- coding: utf-8 -*-
"""
Visible Layers Locator (prefix: 'vls')
Search only among EFFECTIVELY visible layers in the current project via the Locator bar.

Compatible with QGIS 3.x (Qt5 / PyQt5) and QGIS 4.x (Qt6 / PyQt6).
"""

from qgis.core import (
    QgsLocatorFilter,
    QgsLocatorResult,
    QgsProject,
    QgsMessageLog,
    Qgis,
)

LOG_TAG = "VisibleLayersLocator"


def _enum(owner, scope, member):
    """
    Resolve an enum value in a way that works for both scoped (QGIS 4 / PyQt6)
    and unscoped (older QGIS 3 / PyQt5) enum access.
    """
    try:
        return getattr(getattr(owner, scope), member)
    except AttributeError:
        return getattr(owner, member)


MSG_INFO = _enum(Qgis, "MessageLevel", "Info")
MSG_CRITICAL = _enum(Qgis, "MessageLevel", "Critical")
PRIORITY_HIGH = _enum(QgsLocatorFilter, "Priority", "High")


def _log(msg, level=MSG_INFO):
    QgsMessageLog.logMessage(f"[{LOG_TAG}] {msg}", LOG_TAG, level)


def _result_user_data(result):
    # QGIS >= 3.18 exposes userData as a method, older versions as an attribute
    ud = result.userData
    return ud() if callable(ud) else ud


def _is_effectively_visible(node):
    """
    True if the layer tree node and ALL of its ancestor groups are checked.
    """
    if hasattr(node, "isVisible"):
        return node.isVisible()
    cur = node
    while cur is not None:
        if hasattr(cur, "itemVisibilityChecked") and not cur.itemVisibilityChecked():
            return False
        cur = cur.parent()
    return True


def _visible_layers():
    """
    Snapshot of (name, layer id) for all effectively visible layers.
    Must be called from the main thread.
    """
    root = QgsProject.instance().layerTreeRoot()
    if root is None:
        return []
    out = []
    for lnode in root.findLayers():
        if not _is_effectively_visible(lnode):
            continue
        lyr = lnode.layer()
        if lyr is None:
            continue
        out.append((lyr.name(), lyr.id()))
    return out


class VisibleLayersLocatorFilter(QgsLocatorFilter):
    """
    Locator filter that searches for effectively visible layers in the current project.
    - Uses the 'vls' prefix (QGIS ignores plugin prefixes shorter than 3 chars).
    - Case-insensitive substring match on layer name.
    - Trigger selects the layer in the Layers panel.
    """

    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self._candidates = None

    def name(self):
        return "VisibleLayersLocator"

    def clone(self):
        return VisibleLayersLocatorFilter(self.iface)

    def displayName(self):
        return "Visible Layer Search"

    def prefix(self):
        return "vls"

    def priority(self):
        return PRIORITY_HIGH

    def prepare(self, string, context):
        # Called on the main thread before fetchResults() runs in a worker thread,
        # so this is the safe place to touch the project / layer tree.
        self._candidates = _visible_layers()
        return []

    def fetchResults(self, search, context, feedback):
        query = (search or "").strip().lower()
        if not query:
            return

        candidates = self._candidates
        if candidates is None:
            # Fallback for QGIS versions without prepare()
            candidates = _visible_layers()

        for name, layer_id in candidates:
            if feedback.isCanceled():
                return
            if query in name.lower():
                result = QgsLocatorResult(self, name, layer_id)
                self.resultFetched.emit(result)

    def triggerResult(self, result):
        layer_id = _result_user_data(result)
        if not layer_id:
            return
        layer = QgsProject.instance().mapLayer(layer_id)
        if layer is None:
            return

        ltv = self.iface.layerTreeView()
        if ltv is None:
            return
        try:
            ltv.setCurrentLayer(layer)
            ltv.setFocus()
        except Exception as e:
            _log(f"Could not select layer: {e}")


class VisibleLayersLocatorPlugin:
    """
    Main plugin that registers the VisibleLayersLocatorFilter with QGIS.
    """

    def __init__(self, iface):
        self.iface = iface
        self.filter = None

    def initGui(self):
        self.filter = VisibleLayersLocatorFilter(self.iface)
        try:
            self.iface.registerLocatorFilter(self.filter)
        except Exception as e:
            _log(f"Failed to register locator filter: {e}", MSG_CRITICAL)

    def unload(self):
        if self.filter:
            try:
                self.iface.deregisterLocatorFilter(self.filter)
            except Exception as e:
                _log(f"Failed to deregister locator filter: {e}", MSG_CRITICAL)
        self.filter = None

/** LTCN brand presentation. Never replace Lit-managed DOM nodes. */
const key = Symbol.for("ltcn_logo_changer");
const previous = window[key];
if (previous?.dispose) previous.dispose();

const params = new URL(import.meta.url).searchParams;
const name = params.get("name") || "";
const revision = params.get("revision") || "";
const nameLength = Array.from(name).length;
const valid = nameLength > 0 && nameLength <= 64 && /^[0-9a-f]{32}$/.test(revision);
let disposed = false;
let observer;
let Sidebar;
let originalWillUpdate;
let brandedWillUpdate;
let warned = false;
const warn = () => {
  if (!warned) console.warn("LTCN LOGO CHANGER: sidebar title is unavailable; navigation is unchanged.");
  warned = true;
};
window[key] = {
  dispose() {
    disposed = true;
    observer?.disconnect();
    if (Sidebar && Sidebar.prototype.willUpdate === brandedWillUpdate) {
      Sidebar.prototype.willUpdate = originalWillUpdate;
    }
  },
};

if (valid) {
  const base = `/local/ltcn_logo_changer/${revision}`;
  // These links belong to the static document head, outside HA's Lit components.
  for (const [rel, file, type] of [
    ["icon", "favicon.ico", "image/x-icon"],
    ["apple-touch-icon", "apple-touch-icon.png", "image/png"],
  ]) {
    let links = [...document.head.querySelectorAll(`link[rel~="${rel}"]`)];
    if (!links.length) {
      const link = document.createElement("link");
      link.rel = rel;
      document.head.append(link);
      links = [link];
    }
    for (const link of links) {
      link.href = `${base}/${file}`;
      link.type = type;
    }
  }

  const updateDocumentTitle = () => {
    const current = document.title;
    if (current === name || [" - ", " – ", " — "].some(separator => current.endsWith(separator + name))) return;
    if (current.endsWith("Home Assistant")) {
      document.title = current.slice(0, -"Home Assistant".length) + name;
    }
  };
  updateDocumentTitle();
  const title = document.head.querySelector("title");
  if (title) {
    observer = new MutationObserver(updateDocumentTitle);
    observer.observe(title, { childList: true, characterData: true, subtree: true });
  }

  customElements.whenDefined("ha-sidebar").then(() => {
    if (disposed) return;
    Sidebar = customElements.get("ha-sidebar");
    // This small compatibility layer is optional. If HA changes its interface,
    // retain the normal sidebar and still apply document icons/title.
    if (!Sidebar?.elementProperties?.has("sidebarTitle") ||
        typeof Sidebar.prototype.willUpdate !== "function") {
      warn();
      return;
    }
    originalWillUpdate = Sidebar.prototype.willUpdate;
    brandedWillUpdate = function(changedProperties) {
      // Preserve Home Assistant's lifecycle and its error behavior.
      originalWillUpdate.call(this, changedProperties);
      try { this.sidebarTitle = name; }
      catch (_) { warn(); }
    };
    Sidebar.prototype.willUpdate = brandedWillUpdate;
  }).catch(warn);
}

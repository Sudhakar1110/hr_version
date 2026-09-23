/* Bizaxl HR Portal - shared runtime (design system aware) */
(function () {
  if (window.__bzPortalLoaded) return;
  window.__bzPortalLoaded = true;

  const BZ = (window.BizaxlPortal = {
    api(name, args) {
      return new Promise((resolve, reject) => {
        frappe.call({
          method: "bizaxl_hrms.bizaxl_hr.api." + name,
          args: args || {},
          callback: (r) => resolve(r && r.message),
          error: (e) => reject(e),
        });
      });
    },
    toast(msg, type) {
      const el = document.createElement("div");
      el.className = "bz-toast";
      const icon =
        window.lucide && lucide.icons.check
          ? lucide.createElement("check-circle").outerHTML
          : "";
      el.innerHTML =
        icon +
        '<span>' +
        (msg || "Done") +
        "</span>";
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 3200);
    },
    fmtMoney(amount) {
      if (amount === null || amount === undefined) return "--";
      const n = Number(amount);
      return "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
    },
    relTime(dt) {
      if (!dt) return "";
      const d = new Date(dt);
      const diff = (Date.now() - d.getTime()) / 1000;
      if (diff < 60) return "just now";
      if (diff < 3600) return Math.floor(diff / 60) + "m ago";
      if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
      if (diff < 604800) return Math.floor(diff / 86400) + "d ago";
      return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
    },
    initials(name) {
      if (!name) return "?";
      return name
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((w) => w[0].toUpperCase())
        .join("");
    },
    esc(text) {
      return String(text == null ? "" : text).replace(
        /[&<>"]/g,
        (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]
      );
    },
    setText(el, v) {
      if (el) el.textContent = v == null ? "" : v;
    },
    pollNotifications() {
      const badge = document.getElementById("bz-notif-count");
      if (!badge) return;
      this.api("notification_unread_count")
        .then((r) => {
          const n = r && r.count ? Number(r.count) : 0;
          const dot = document.getElementById("bz-notif-dot");
          if (dot) dot.style.display = n > 0 ? "block" : "none";
        })
        .catch(() => {});
    },
    initIcons() {
      if (window.lucide && lucide.createIcons && lucide.icons) {
        try {
          lucide.createIcons();
        } catch (e) {}
      }
    },
  });

  document.addEventListener("DOMContentLoaded", () => {
    BZ.initIcons();
    BZ.pollNotifications();
    setInterval(() => BZ.pollNotifications(), 60000);

    // Re-iconify dynamically injected <i data-lucide> elements
    let _deb;
    if (window.MutationObserver && window.lucide) {
      new MutationObserver(() => {
        clearTimeout(_deb);
        _deb = setTimeout(() => {
          try { lucide.createIcons(); } catch (e) {}
        }, 60);
      }).observe(document.body, { childList: true, subtree: true });
    }

    const params = new URLSearchParams(window.location.search);
    const toastMsg = params.get("msg");
    if (toastMsg) setTimeout(() => BZ.toast(decodeURIComponent(toastMsg)), 300);
  });
})();
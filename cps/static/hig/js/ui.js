/*
 * Behavior for the redesigned interface's components. No dependencies.
 *
 *   Menus:   <button data-ui-menu="menu-id" aria-expanded="false"> ... <div id="menu-id" class="ui-menu" hidden>
 *   Dialogs: <button data-ui-open="dialog-id"> opens a <dialog class="ui-sheet|ui-alert">;
 *            [data-ui-close] inside it closes it.
 *   Toasts:  ui.toast("Saved", {tone: "success"})
 *   Appearance: ui.setAppearance("auto" | "light" | "dark")
 */
(function () {
    "use strict";

    var APPEARANCE_KEY = "ui-appearance";
    var TOAST_ICONS = {success: "circle-check", error: "circle-x", warning: "triangle-alert", info: "info"};
    var spriteUrl = (document.currentScript && document.currentScript.dataset.sprite) || "";

    // ---- Appearance ----

    function getAppearance() {
        try {
            return localStorage.getItem(APPEARANCE_KEY) || "auto";
        } catch (e) {
            return "auto";
        }
    }

    function applyAppearance(value) {
        // A page that only exists in one appearance pins it and opts out of the reader's choice
        if (document.documentElement.hasAttribute("data-appearance-lock")) {
            return;
        }
        if (value === "light" || value === "dark") {
            document.documentElement.dataset.appearance = value;
        } else {
            delete document.documentElement.dataset.appearance;
        }
    }

    function setAppearance(value) {
        try {
            localStorage.setItem(APPEARANCE_KEY, value);
        } catch (e) { /* private browsing: applies to this page only */ }
        applyAppearance(value);
        document.dispatchEvent(new CustomEvent("ui:appearance", {detail: value}));
    }

    // Applied as soon as the script runs, so a pinned appearance does not flash the other one
    applyAppearance(getAppearance());

    // ---- Menus ----

    var openMenu = null;

    function menuItems(menu) {
        return Array.prototype.slice.call(menu.querySelectorAll(".ui-menu-item:not([disabled])"));
    }

    function closeMenu(returnFocus) {
        if (!openMenu) {
            return;
        }
        openMenu.menu.hidden = true;
        openMenu.trigger.setAttribute("aria-expanded", "false");
        if (returnFocus) {
            openMenu.trigger.focus();
        }
        openMenu = null;
    }

    function showMenu(trigger, menu) {
        closeMenu(false);
        menu.hidden = false;
        trigger.setAttribute("aria-expanded", "true");
        openMenu = {trigger: trigger, menu: menu};
        // Flip to the other edge if the menu would leave the viewport
        menu.classList.remove("ui-menu--end");
        if (menu.getBoundingClientRect().right > window.innerWidth - 8) {
            menu.classList.add("ui-menu--end");
        }
    }

    document.addEventListener("click", function (event) {
        var trigger = event.target.closest("[data-ui-menu]");
        if (trigger) {
            var menu = document.getElementById(trigger.dataset.uiMenu);
            if (!menu) {
                return;
            }
            if (openMenu && openMenu.menu === menu) {
                closeMenu(false);
            } else {
                showMenu(trigger, menu);
            }
            return;
        }
        if (openMenu && (!openMenu.menu.contains(event.target) || event.target.closest(".ui-menu-item"))) {
            closeMenu(false);
        }
    });

    document.addEventListener("keydown", function (event) {
        if (!openMenu) {
            return;
        }
        var items = menuItems(openMenu.menu);
        var index = items.indexOf(document.activeElement);
        if (event.key === "Escape") {
            closeMenu(true);
        } else if (event.key === "ArrowDown") {
            event.preventDefault();
            items[(index + 1) % items.length].focus();
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            items[(index - 1 + items.length) % items.length].focus();
        } else if (event.key === "Tab") {
            closeMenu(false);
        }
    });

    // ---- Sheets and alerts ----

    document.addEventListener("click", function (event) {
        var opener = event.target.closest("[data-ui-open]");
        if (opener) {
            var dialog = document.getElementById(opener.dataset.uiOpen);
            if (dialog && typeof dialog.showModal === "function") {
                dialog.showModal();
            }
            return;
        }
        var closer = event.target.closest("[data-ui-close]");
        if (closer) {
            var parent = closer.closest("dialog");
            if (parent) {
                parent.close(closer.value || "");
            }
            return;
        }
        // A click on the backdrop lands on the <dialog> itself; sheets dismiss, alerts need an answer
        if (event.target.matches && event.target.matches("dialog.ui-sheet")) {
            var box = event.target.getBoundingClientRect();
            var inside = event.clientX >= box.left && event.clientX <= box.right &&
                event.clientY >= box.top && event.clientY <= box.bottom;
            if (!inside) {
                event.target.close();
            }
        }
    });

    // ---- Toasts ----

    function toastRegion() {
        var region = document.querySelector(".ui-toast-region");
        if (!region) {
            region = document.createElement("div");
            region.className = "ui-toast-region";
            region.setAttribute("role", "status");
            region.setAttribute("aria-live", "polite");
            document.body.appendChild(region);
        }
        return region;
    }

    function toast(message, options) {
        options = options || {};
        var tone = TOAST_ICONS[options.tone] ? options.tone : "info";
        var element = document.createElement("div");
        element.className = "ui-toast ui-toast--" + tone;
        if (spriteUrl) {
            var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            var use = document.createElementNS("http://www.w3.org/2000/svg", "use");
            svg.setAttribute("class", "ui-icon");
            svg.setAttribute("aria-hidden", "true");
            use.setAttribute("href", spriteUrl + "#" + TOAST_ICONS[tone]);
            svg.appendChild(use);
            element.appendChild(svg);
        }
        var text = document.createElement("span");
        text.textContent = message;
        element.appendChild(text);
        toastRegion().appendChild(element);

        var duration = options.duration === undefined ? 4000 : options.duration;
        function dismiss() {
            element.classList.add("is-leaving");
            setTimeout(function () {
                element.remove();
            }, 300);
        }
        if (duration > 0) {
            setTimeout(dismiss, duration);
        }
        element.addEventListener("click", dismiss);
        return element;
    }

    window.ui = {
        toast: toast,
        getAppearance: getAppearance,
        setAppearance: setAppearance,
        closeMenu: closeMenu
    };
})();

/*
 * Behavior of the application frame (hig/shell.html): the navigation drawer on narrow
 * windows, server-rendered toasts, the collapsed state of sidebar groups and library refresh.
 * Depends on ui.js.
 */
(function () {
    "use strict";

    var script = document.currentScript;
    var root = document.documentElement;

    // ---- Navigation drawer (narrow windows) ----

    function setNavOpen(open) {
        if (open) {
            root.dataset.navOpen = "";
        } else {
            delete root.dataset.navOpen;
        }
        var toggles = document.querySelectorAll("[data-ui-nav-open]");
        for (var i = 0; i < toggles.length; i++) {
            toggles[i].setAttribute("aria-expanded", open ? "true" : "false");
        }
    }

    document.addEventListener("click", function (event) {
        if (event.target.closest("[data-ui-nav-open]")) {
            setNavOpen(!("navOpen" in root.dataset));
        } else if (event.target.closest("[data-ui-nav-close]")) {
            setNavOpen(false);
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && "navOpen" in root.dataset) {
            setNavOpen(false);
        }
    });

    // ---- Sidebar groups remember whether they are collapsed ----

    var groups = document.querySelectorAll(".ui-sidebar details");
    Array.prototype.forEach.call(groups, function (group, index) {
        var key = "ui-sidebar-group-" + index;
        try {
            if (localStorage.getItem(key) === "closed") {
                group.open = false;
            }
            group.addEventListener("toggle", function () {
                localStorage.setItem(key, group.open ? "open" : "closed");
            });
        } catch (e) { /* storage unavailable: groups just start open */ }
    });

    // Keep the current page's entry in view when the sidebar is long
    var current = document.querySelector(".ui-sidebar [aria-current]");
    if (current && current.scrollIntoView) {
        current.scrollIntoView({block: "nearest"});
    }

    // ---- Server-rendered toasts ----

    function dismissToast(toast) {
        toast.classList.add("is-leaving");
        setTimeout(function () {
            toast.remove();
        }, 300);
    }

    Array.prototype.forEach.call(document.querySelectorAll(".ui-toast[data-ui-autodismiss]"), function (toast) {
        setTimeout(function () {
            dismissToast(toast);
        }, 6000);
    });

    document.addEventListener("click", function (event) {
        var close = event.target.closest("[data-ui-toast-close]");
        if (!close) {
            return;
        }
        if (close.dataset.dismissUrl) {
            fetch(close.dataset.dismissUrl, {method: "POST", headers: {"X-CSRFToken": script.dataset.csrf}});
        }
        dismissToast(close.closest(".ui-toast"));
    });

    // ---- Upload from the toolbar ----

    var uploadForm = document.getElementById("ui-upload-form");
    var uploadInput = document.getElementById("ui-upload-input");

    function uploadFiles(files) {
        var data = new FormData();
        data.append("csrf_token", uploadForm.elements.csrf_token.value);
        Array.prototype.forEach.call(files, function (file) {
            data.append(uploadInput.name, file);
        });

        var toast = window.ui.toast(uploadForm.dataset.uploading, {tone: "info", duration: 0});
        var bar = document.createElement("progress");
        bar.className = "ui-progress ui-toast-progress";
        bar.max = 100;
        bar.value = 0;
        toast.appendChild(bar);

        function fail() {
            toast.remove();
            window.ui.toast(uploadForm.dataset.failed, {tone: "error"});
        }

        var request = new XMLHttpRequest();
        request.open("POST", uploadForm.action);
        request.upload.addEventListener("progress", function (event) {
            if (event.lengthComputable) {
                bar.value = Math.round(event.loaded / event.total * 100);
            }
        });
        request.addEventListener("load", function () {
            var location = null;
            try {
                location = JSON.parse(request.responseText).location;
            } catch (e) { /* not JSON: treated as a failure below */ }
            if (request.status >= 200 && request.status < 300 && location) {
                toast.querySelector("span").textContent = uploadForm.dataset.done;
                window.location.href = location;
            } else {
                fail();
            }
        });
        request.addEventListener("error", fail);
        request.send(data);
    }

    if (uploadForm && uploadInput) {
        uploadInput.addEventListener("change", function () {
            if (uploadInput.files.length > 0) {
                uploadFiles(uploadInput.files);
                uploadInput.value = "";
            }
        });
    }

    // ---- Library refresh ----

    var refreshTimer = null;

    function plainText(html) {
        var holder = document.createElement("div");
        holder.innerHTML = html;
        return holder.textContent.trim();
    }

    function pollRefreshMessages() {
        fetch(script.dataset.refreshMessagesUrl)
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.messages && data.messages.length > 0) {
                    clearInterval(refreshTimer);
                    refreshTimer = null;
                    data.messages.forEach(function (message) {
                        window.ui.toast(plainText(message), {tone: "info", duration: 8000});
                    });
                }
            })
            .catch(function () {
                clearInterval(refreshTimer);
                refreshTimer = null;
            });
    }

    window.refreshLibrary = function () {
        if (!script.dataset.refreshUrl || refreshTimer) {
            return;
        }
        fetch(script.dataset.refreshUrl, {method: "POST", headers: {"Content-Type": "application/json", "X-CSRFToken": script.dataset.csrf}})
            .then(function (response) { return response.json(); })
            .then(function (data) {
                window.ui.toast(plainText(data.message), {tone: "info"});
                refreshTimer = setInterval(pollRefreshMessages, 1000);
            })
            .catch(function () {
                window.ui.toast(script.dataset.error, {tone: "error"});
            });
    };
})();

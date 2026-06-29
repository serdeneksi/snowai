/**
 * SnowAI — Zabbix Problems Sayfası AI Entegrasyonu
 * Konum: /usr/share/zabbix/js/snowai.js
 *
 * Görev:
 *  1. Problems tablosundaki her satıra "AI Analiz" butonu ekler.
 *  2. Butona tıklandığında popup açar.
 *  3. /ai/analyze endpoint'ine POST atar, sonucu gösterir.
 */

(function () {
    "use strict";

    /* ── Sabitler ─────────────────────────────────────────────────────── */
    var ANALYZE_URL = "/ai/analyze";
    var POLL_INTERVAL = 1200;   // ms — tablo değişikliklerini kontrol aralığı
    var PROCESSED_ATTR = "data-snowai-done";

    var SEV_LABELS = {
        "0": "Not classified",
        "1": "Information",
        "2": "Warning",
        "3": "Average",
        "4": "High",
        "5": "Disaster"
    };

    /* ── Popup HTML ───────────────────────────────────────────────────── */
    function buildPopupDOM() {
        if (document.getElementById("snowai-overlay")) return;

        var overlay = document.createElement("div");
        overlay.id = "snowai-overlay";
        overlay.addEventListener("click", closePopup);

        var popup = document.createElement("div");
        popup.id = "snowai-popup";
        popup.setAttribute("role", "dialog");
        popup.setAttribute("aria-modal", "true");
        popup.innerHTML = [
            '<div id="snowai-header">',
            '  <div id="snowai-logo">✦</div>',
            '  <span id="snowai-title">SnowAI — Alarm Analizi</span>',
            '  <button id="snowai-close" title="Kapat" onclick="(function(){document.getElementById(\'snowai-overlay\').classList.remove(\'active\');document.getElementById(\'snowai-popup\').classList.remove(\'active\');})()">✕</button>',
            '</div>',
            '<div id="snowai-meta"></div>',
            '<div id="snowai-body">',
            '  <div id="snowai-loading">',
            '    <div class="snowai-spinner"></div>',
            '    <span>Yapay zeka analiz ediyor…</span>',
            '  </div>',
            '  <div id="snowai-error"></div>',
            '  <div id="snowai-result" style="display:none;flex-direction:column;gap:12px;"></div>',
            '</div>'
        ].join("");

        document.body.appendChild(overlay);
        document.body.appendChild(popup);

        /* ESC ile kapat */
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") closePopup();
        });
    }

    function closePopup() {
        var o = document.getElementById("snowai-overlay");
        var p = document.getElementById("snowai-popup");
        if (o) o.classList.remove("active");
        if (p) p.classList.remove("active");
    }

    function openPopup() {
        var o = document.getElementById("snowai-overlay");
        var p = document.getElementById("snowai-popup");
        if (o) o.classList.add("active");
        if (p) p.classList.add("active");
    }

    /* ── Popup İçerik Yönetimi ────────────────────────────────────────── */
    function resetPopup() {
        document.getElementById("snowai-meta").innerHTML = "";
        document.getElementById("snowai-loading").style.display = "flex";
        document.getElementById("snowai-error").style.display = "none";
        document.getElementById("snowai-error").textContent = "";
        var result = document.getElementById("snowai-result");
        result.style.display = "none";
        result.innerHTML = "";
    }

    function showMeta(host, problem, sevKey) {
        var sevLabel = SEV_LABELS[String(sevKey)] || sevKey || "—";
        var sevClass = "sev-" + (sevKey || "0");
        document.getElementById("snowai-meta").innerHTML =
            '<span class="snowai-badge host">🖥 ' + escHtml(host || "—") + '</span>' +
            '<span class="snowai-badge ' + sevClass + '">⚡ ' + escHtml(sevLabel) + '</span>';
    }

    function showResult(data) {
        document.getElementById("snowai-loading").style.display = "none";

        var urgencyClass = "snowai-urgency-" + (data.urgency || "Orta");
        var result = document.getElementById("snowai-result");
        result.style.display = "flex";
        result.innerHTML = [
            /* Problem adı */
            '<div class="snowai-card">',
            '  <div class="snowai-card-label">Problem</div>',
            '  <div class="snowai-card-text">' + escHtml(data.problem || "—") + '</div>',
            '</div>',
            /* AI analizi */
            '<div class="snowai-card">',
            '  <div class="snowai-card-label">Yapay Zeka Analizi</div>',
            '  <div class="snowai-card-text">' + escHtml(data.analysis || "—") + '</div>',
            '</div>',
            /* Aciliyet */
            '<div class="snowai-card">',
            '  <div class="snowai-card-label">Aciliyet</div>',
            '  <div class="snowai-card-text ' + urgencyClass + '">' + escHtml(data.urgency || "Orta") + '</div>',
            '</div>',
            /* Ekip & Kanal */
            '<div id="snowai-team-row">',
            '  <div class="snowai-card">',
            '    <div class="snowai-card-label">Sorumlu Ekip</div>',
            '    <div class="snowai-card-text">' + escHtml(data.team || "—") + '</div>',
            '  </div>',
            '  <div class="snowai-card">',
            '    <div class="snowai-card-label">Kanal</div>',
            '    <div class="snowai-card-text">#' + escHtml(data.channel || "—") + '</div>',
            '  </div>',
            '</div>',
            /* Önerilen Aksiyon */
            '<div class="snowai-card">',
            '  <div class="snowai-card-label">Önerilen Aksiyon</div>',
            '  <div class="snowai-card-text">' + escHtml(data.action || "—") + '</div>',
            '</div>'
        ].join("");
    }

    function showError(msg) {
        document.getElementById("snowai-loading").style.display = "none";
        var el = document.getElementById("snowai-error");
        el.style.display = "block";
        el.textContent = "⚠ " + msg;
    }

    /* ── API Çağrısı ──────────────────────────────────────────────────── */
    function analyze(problem, host, severity, duration) {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", ANALYZE_URL, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.timeout = 20000;

        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    showResult(data);
                } catch (e) {
                    showError("Sunucu yanıtı ayrıştırılamadı.");
                }
            } else {
                showError("Servis hatası: HTTP " + xhr.status);
            }
        };

        xhr.onerror = function () {
            showError("SnowAI servisine bağlanılamadı. /ai/analyze adresini kontrol edin.");
        };

        xhr.ontimeout = function () {
            showError("İstek zaman aşımına uğradı (20 sn).");
        };

        xhr.send(JSON.stringify({
            problem:  problem,
            host:     host,
            severity: severity,
            duration: duration
        }));
    }

    /* ── Tablo Tarama & Buton Ekleme ──────────────────────────────────── */

    /**
     * Problems tablosundaki satırlardan veri çıkarır.
     * Zabbix 6.x ve 7.x tablo yapısını destekler.
     */
    function extractRowData(row) {
        var cells = row.querySelectorAll("td");
        if (cells.length < 3) return null;

        /* Severity: genellikle "severity" class'ı taşıyan hücre */
        var sevCell = row.querySelector("td.severity, td[class*='disaster'], td[class*='high'], td[class*='average'], td[class*='warning'], td[class*='information']");
        var sevKey = "0";
        if (sevCell) {
            var cls = sevCell.className || "";
            if      (cls.indexOf("disaster")    !== -1) sevKey = "5";
            else if (cls.indexOf("high")        !== -1) sevKey = "4";
            else if (cls.indexOf("average")     !== -1) sevKey = "3";
            else if (cls.indexOf("warning")     !== -1) sevKey = "2";
            else if (cls.indexOf("information") !== -1) sevKey = "1";
        }

        /* Host adı: "host" veya "hosts" class'ı taşıyan hücre */
        var hostCell = row.querySelector("td.host, td.hosts, td[class*='host']");
        var host = hostCell ? hostCell.textContent.trim() : "";

        /* Problem adı: "problem" class'ı veya en uzun metin içeren td */
        var probCell = row.querySelector("td.problem, td[class*='problem'], td.name");
        var problem = "";
        if (probCell) {
            problem = probCell.textContent.trim();
        } else {
            /* Fallback: en uzun metinli hücreyi seç */
            var maxLen = 0;
            cells.forEach(function (td) {
                var t = td.textContent.trim();
                if (t.length > maxLen) { maxLen = t.length; problem = t; }
            });
        }

        /* Süre */
        var durCell = row.querySelector("td.duration, td[class*='duration']");
        var duration = durCell ? durCell.textContent.trim() : "";

        return { problem: problem, host: host, severity: sevKey, duration: duration };
    }

    function addButtonToRow(row) {
        if (row.getAttribute(PROCESSED_ATTR)) return;
        row.setAttribute(PROCESSED_ATTR, "1");

        /* Zaman başlığı satırlarını atla (Yesterday, June, vb.) */
        var cls = row.className || "";
        if (
            cls.indexOf("hover-nobg") !== -1 ||
            cls.indexOf("group_row") !== -1 ||
            cls.indexOf("header") !== -1 ||
            row.querySelector("th") !== null
        ) return;

        /* Tek hücre span ile dolu satırları atla */
        var firstCell = row.cells[0];
        if (firstCell) {
            var colspan = parseInt(firstCell.getAttribute("colspan") || "1", 10);
            if (colspan > 3) return;
        }

        var data = extractRowData(row);
        if (!data || !data.problem) return;

        /* Buton hücresini bul veya oluştur */
        var lastCell = row.querySelector("td.action, td.actions");
        if (!lastCell) {
            lastCell = row.cells[row.cells.length - 1];
        }
        if (!lastCell) return;

        var btn = document.createElement("button");
        btn.className = "snowai-btn";
        btn.title = "SnowAI ile analiz et";
        btn.innerHTML =
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8">' +
            '<circle cx="8" cy="8" r="6.5"/>' +
            '<path d="M8 5v3.5l2 2" stroke-linecap="round"/>' +
            '</svg> AI Analiz';

        /* Snapshot alarak closure sorununu önle */
        (function (d) {
            btn.addEventListener("click", function (e) {
                e.stopPropagation();
                resetPopup();
                showMeta(d.host, d.problem, d.severity);
                openPopup();
                analyze(d.problem, d.host, d.severity, d.duration);
            });
        }(data));

        /* Hücre içeriğini bozmadan ekle */
        var wrapper = document.createElement("span");
        wrapper.style.marginLeft = "6px";
        wrapper.appendChild(btn);
        lastCell.appendChild(wrapper);
    }

    function isProblemsPage() {
        /* Sadece Problems sayfasında veya Problems widget içinde çalış */
        var url = window.location.href;
        return (
            url.indexOf("zabbix.php?action=problem") !== -1 ||
            url.indexOf("zabbix.php?action=dashboard") !== -1 ||
            url.indexOf("tr_events.php") !== -1 ||
            document.querySelector(".list-table td.severity, .list-table td[class*='high'], .list-table td[class*='disaster'], .list-table td[class*='average'], .list-table td[class*='warning']") !== null
        );
    }

    function scanTable() {
        /* Sadece severity sütunu olan tablolarda çalış */
        if (!isProblemsPage()) return;

        var rows = document.querySelectorAll(".list-table tbody tr");
        rows.forEach(function(row) {
            /* Satırda severity sütunu yoksa atla — Hosts tablosu gibi sayfaları filtreler */
            var hasSeverity = row.querySelector(
                "td.severity, td[class*='disaster'], td[class*='high'], td[class*='average'], td[class*='warning'], td[class*='information']"
            );
            if (!hasSeverity) return;
            addButtonToRow(row);
        });
    }

    /* ── Başlatma ─────────────────────────────────────────────────────── */
    function init() {
        buildPopupDOM();
        scanTable();

        /* Tablo dinamik yüklenebilir, periyodik tara */
        setInterval(scanTable, POLL_INTERVAL);

        /* MutationObserver ile anlık değişiklikleri yakala */
        var observer = new MutationObserver(function () {
            scanTable();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    /* DOM hazır olduğunda başlat */
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    /* ── Yardımcı ─────────────────────────────────────────────────────── */
    function escHtml(str) {
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

}());

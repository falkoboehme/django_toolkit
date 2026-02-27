
function DependencySelectAjax(url, target_id, selected_ids=[]) {
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // clean the target select field
            $(`#${target_id}`).empty();

            // add options to the target select field
            $.each(data.results, function(index, value) {
                $(`#${target_id}`).append($('<option>', {
                    value: value.id,
                    text: value.display,
                    selected: selected_ids.includes(value.id),
                }));
            });
        })
        .catch(error => console.error('Error:', error));
}

// --- Drag and Drop functions start ---
// function IsBefore(a, b) {
//     if (a.parentNode == b.parentNode) {
//         for (var cur = a; cur; cur = cur.previousSibling) {
//             if (cur === b) {
//                 return true;
//             }
//         }
//     }
//     return false;
// }

// function DragEnter(e) {
//     var targetelem = e.target;
//     if (targetelem.nodeName == "TD") {
//        targetelem = targetelem.parentNode;   
//     }  

//     if (IsBefore(source, targetelem)) {
//         targetelem.parentNode.insertBefore(source, targetelem);
//     } else {
//         targetelem.parentNode.insertBefore(source, targetelem.nextSibling);
//     }
// }

// function DragStart(e) {
//     source = e.target;
//     e.dataTransfer.effectAllowed = 'move';
// }
// --- Drag and Drop functions end ---

function initializeSidebarController() {
    const layout = document.getElementById('dtk-layout');
    const sidebar = document.getElementById('dtk-sidenav');
    const resizer = document.getElementById('dtk-sidenav-resize');
    const toggle = document.getElementById('dtk-sidebar-toggle');

    if (!layout || !sidebar || !resizer || !toggle) {
        return;
    }

    const STORAGE_WIDTH = 'dtk.sidebar.width';
    const STORAGE_COLLAPSED = 'dtk.sidebar.collapsed';
    const MIN_WIDTH = 180;
    const MAX_WIDTH = 320;
    const DEFAULT_WIDTH = 220;
    const COLLAPSED_WIDTH = 0;

    function clampWidth(width) {
        return Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, width));
    }

    function setSidebarWidth(width) {
        const normalizedWidth = clampWidth(width);
        layout.style.setProperty('--dtk-sidebar-width', `${normalizedWidth}px`);
        localStorage.setItem(STORAGE_WIDTH, String(normalizedWidth));
        return normalizedWidth;
    }

    function isCollapsed() {
        return layout.classList.contains('dtk-sidebar-collapsed');
    }

    function setCollapsed(collapsed) {
        layout.classList.toggle('dtk-sidebar-collapsed', collapsed);
        layout.style.setProperty('--dtk-sidebar-width', collapsed ? `${COLLAPSED_WIDTH}px` : `${setSidebarWidth(getSavedWidth())}px`);
        toggle.setAttribute('aria-expanded', String(!collapsed));
        localStorage.setItem(STORAGE_COLLAPSED, collapsed ? '1' : '0');
    }

    function getSavedWidth() {
        const storedWidth = parseInt(localStorage.getItem(STORAGE_WIDTH) || `${DEFAULT_WIDTH}`, 10);
        if (Number.isNaN(storedWidth)) {
            return DEFAULT_WIDTH;
        }
        return clampWidth(storedWidth);
    }

    function getSavedCollapsed() {
        return localStorage.getItem(STORAGE_COLLAPSED) === '1';
    }

    function toggleCollapsed() {
        setCollapsed(!isCollapsed());
    }

    toggle.addEventListener('click', toggleCollapsed);

    let isDragging = false;

    function onPointerMove(event) {
        if (!isDragging || isCollapsed()) {
            return;
        }
        const nextWidth = clampWidth(event.clientX);
        layout.style.setProperty('--dtk-sidebar-width', `${nextWidth}px`);
    }

    function onPointerUp() {
        if (!isDragging) {
            return;
        }
        isDragging = false;
        document.body.classList.remove('dtk-resizing-sidebar');
        const renderedWidth = parseInt(getComputedStyle(layout).getPropertyValue('--dtk-sidebar-width'), 10);
        if (!Number.isNaN(renderedWidth)) {
            setSidebarWidth(renderedWidth);
        }
        window.removeEventListener('pointermove', onPointerMove);
        window.removeEventListener('pointerup', onPointerUp);
    }

    resizer.addEventListener('pointerdown', function (event) {
        if (isCollapsed()) {
            return;
        }
        isDragging = true;
        document.body.classList.add('dtk-resizing-sidebar');
        window.addEventListener('pointermove', onPointerMove);
        window.addEventListener('pointerup', onPointerUp);
        event.preventDefault();
    });

    resizer.addEventListener('keydown', function (event) {
        if (isCollapsed()) {
            return;
        }
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') {
            return;
        }
        const delta = event.key === 'ArrowLeft' ? -16 : 16;
        const currentWidth = parseInt(getComputedStyle(layout).getPropertyValue('--dtk-sidebar-width'), 10) || getSavedWidth();
        setSidebarWidth(currentWidth + delta);
        layout.style.setProperty('--dtk-sidebar-width', `${getSavedWidth()}px`);
        event.preventDefault();
    });

    setSidebarWidth(getSavedWidth());
    setCollapsed(getSavedCollapsed());
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSidebarController);
} else {
    initializeSidebarController();
}
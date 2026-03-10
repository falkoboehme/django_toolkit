
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

function initializeFilterFormSubmitCleanup() {
    const forms = document.querySelectorAll('form[data-dt-filter-form="true"]');

    forms.forEach(function (form) {
        if (form.dataset.dtFilterBound === 'true') {
            return;
        }

        form.dataset.dtFilterBound = 'true';

        form.addEventListener('submit', function () {
            const filterPrefix = form.dataset.dtFilterPrefix || 'filter__';
            const fields = form.querySelectorAll(`[name^="${filterPrefix}"]`);

            fields.forEach(function (field) {
                const fieldValue = String(field.value || '').trim();
                field.disabled = fieldValue === '';
            });
        });
    });
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
    const layout = document.getElementById('dt-layout');
    const sidebar = document.getElementById('dt-sidenav');
    const resizer = document.getElementById('dt-sidenav-resize');
    const toggle = document.getElementById('dt-sidebar-toggle');

    if (!layout || !sidebar || !resizer || !toggle) {
        return;
    }

    const STORAGE_WIDTH = 'dt.sidebar.width';
    const STORAGE_COLLAPSED = 'dt.sidebar.collapsed';
    const MIN_WIDTH = 190;
    const MAX_WIDTH = 300;
    const DEFAULT_WIDTH = 220;
    const COLLAPSED_WIDTH = 0;

    function updateToggleIcon(collapsed) {
        const icon = toggle.querySelector('.dt-sidebar-toggle-icon');
        if (!icon) {
            return;
        }

        const expandedIcon = toggle.dataset.iconExpanded;
        const collapsedIcon = toggle.dataset.iconCollapsed;

        if (collapsed && collapsedIcon) {
            icon.setAttribute('src', collapsedIcon);
            return;
        }

        if (!collapsed && expandedIcon) {
            icon.setAttribute('src', expandedIcon);
        }
    }

    function clampWidth(width) {
        return Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, width));
    }

    function setSidebarWidth(width) {
        const normalizedWidth = clampWidth(width);
        layout.style.setProperty('--dt-sidebar-width', `${normalizedWidth}px`);
        localStorage.setItem(STORAGE_WIDTH, String(normalizedWidth));
        return normalizedWidth;
    }

    function isCollapsed() {
        return layout.classList.contains('dt-sidebar-collapsed');
    }

    function setCollapsed(collapsed) {
        layout.classList.toggle('dt-sidebar-collapsed', collapsed);
        layout.style.setProperty('--dt-sidebar-width', collapsed ? `${COLLAPSED_WIDTH}px` : `${setSidebarWidth(getSavedWidth())}px`);
        toggle.setAttribute('aria-expanded', String(!collapsed));
        updateToggleIcon(collapsed);
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
        layout.style.setProperty('--dt-sidebar-width', `${nextWidth}px`);
    }

    function onPointerUp() {
        if (!isDragging) {
            return;
        }
        isDragging = false;
        document.body.classList.remove('dt-resizing-sidebar');
        const renderedWidth = parseInt(getComputedStyle(layout).getPropertyValue('--dt-sidebar-width'), 10);
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
        document.body.classList.add('dt-resizing-sidebar');
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
        const currentWidth = parseInt(getComputedStyle(layout).getPropertyValue('--dt-sidebar-width'), 10) || getSavedWidth();
        setSidebarWidth(currentWidth + delta);
        layout.style.setProperty('--dt-sidebar-width', `${getSavedWidth()}px`);
        event.preventDefault();
    });

    setSidebarWidth(getSavedWidth());
    setCollapsed(getSavedCollapsed());
}

function initializeDjangoToolkit() {
    initializeSidebarController();
    initializeFilterFormSubmitCleanup();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDjangoToolkit);
} else {
    initializeDjangoToolkit();
}